"""Entry point for the Raspberry Pi SAR runtime."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent
parent_dir = script_dir.parent

if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import serial

if __package__ in (None, ""):
    from pipeline import SARPiPipeline
    from protocol import frame_serial_message
    from test_mode import run_test_mode
else:
    from ras_final.pipeline import SARPiPipeline
    from ras_final.protocol import frame_serial_message
    from ras_final.test_mode import run_test_mode


def _safe_send(serial_conn: serial.Serial | None, message: str, logger: logging.Logger, port: str, baudrate: int) -> serial.Serial | None:
    if not message:
        return serial_conn
    try:
        if serial_conn is None or not serial_conn.is_open:
            serial_conn = serial.Serial(port, baudrate, timeout=2)
        payload = frame_serial_message(message).encode("utf-8")
        serial_conn.write(payload)
        serial_conn.write(b"\n")
        logger.info("Generated message sent to ESP32 over UART: %s", message)
        return serial_conn
    except (serial.SerialException, OSError) as exc:
        logger.warning("UART send failed to %s (%s); skipping this cycle", port, exc)
        if serial_conn is not None:
            try:
                serial_conn.close()
            except OSError:
                pass
        return None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Raspberry Pi SAR pipeline")
    parser.add_argument("--source", type=str, default=None, help="Camera index, video path, or image path")
    parser.add_argument("--weights", type=str, default=None, help="YOLO weights path")
    parser.add_argument("--serial-port", type=str, default="/dev/ttyUSB0", help="UART port to the first ESP32")
    parser.add_argument("--baudrate", type=int, default=115200, help="UART baud rate")
    parser.add_argument("--reconnect-interval", type=float, default=5.0, help="Backoff seconds before reopening UART after a failed send")
    parser.add_argument("--test", action="store_true", help="Print the grid-output smoke-test string")
    parser.add_argument("--once", action="store_true", help="Process a single scan and exit")
    args = parser.parse_args()

    if args.test:
        run_test_mode()
        return

    pipeline = SARPiPipeline(source=args.source, weights=args.weights)
    serial_conn: serial.Serial | None = None
    last_reconnect_attempt = 0.0
    logger = logging.getLogger("pi")

    try:
        if args.once:
            result = pipeline.run_cycle()
            logger.info("Generated message: %s", result.serialized)
            serial_conn = _safe_send(serial_conn, result.serialized, logger, args.serial_port, args.baudrate)
            return

        while True:
            pipeline.generate_next_async()
            time.sleep(30)
            pipeline.swap_if_ready()
            if not pipeline.current_result.serialized:
                continue

            logger.info("Generated message: %s", pipeline.current_result.serialized)
            if serial_conn is None:
                now = time.monotonic()
                if (now - last_reconnect_attempt) < args.reconnect_interval:
                    continue
                last_reconnect_attempt = now

            serial_conn = _safe_send(serial_conn, pipeline.current_result.serialized, logger, args.serial_port, args.baudrate)
    finally:
        if serial_conn is not None:
            try:
                serial_conn.close()
            except OSError:
                pass
        pipeline.camera.close()


if __name__ == "__main__":
    main()
