"""Entry point for the Raspberry Pi SAR runtime."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ras_final.lora_sender import LoRaSender
from ras_final.pipeline import SARPiPipeline
from ras_final.test_mode import run_test_mode


def _safe_send(sender: LoRaSender, message: str, logger: logging.Logger) -> bool:
    """Send the documented JSON payload, retaining no alternate wire format."""
    if not message:
        return False
    try:
        sender.send_text(message)
        logger.info("Compact JSON payload sent to ESP32 over UART: %s", message)
        return True
    except OSError as exc:
        logger.warning("UART send failed to %s (%s); skipping this cycle", sender.port, exc)
        sender.close()
        return False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Raspberry Pi SAR pipeline")
    parser.add_argument("--source", type=str, default=None, help="Camera index, video path, or image path")
    parser.add_argument("--weights", type=str, default=None, help="YOLO weights path")
    parser.add_argument("--serial-port", type=str, default="/dev/ttyUSB0", help="UART port to the first ESP32")
    parser.add_argument("--baudrate", type=int, default=115200, help="UART baud rate")
    parser.add_argument("--reconnect-interval", type=float, default=5.0, help="Backoff seconds before reopening UART after a failed send")
    parser.add_argument("--test", action="store_true", help="Run compact-payload smoke test")
    parser.add_argument("--once", action="store_true", help="Process a single scan and exit")
    args = parser.parse_args()

    if args.test:
        run_test_mode()
        return

    pipeline = SARPiPipeline(source=args.source, weights=args.weights)
    sender = LoRaSender(args.serial_port, args.baudrate)
    last_reconnect_attempt = 0.0
    logger = logging.getLogger("pi")

    try:
        if args.once:
            result = pipeline.run_cycle()
            logger.info("Generated payload: %s", result.payload)
            _safe_send(sender, result.payload, logger)
            return

        while True:
            pipeline.generate_next_async()
            time.sleep(30)
            pipeline.swap_if_ready()
            if not pipeline.current_result.payload:
                continue

            logger.info("Generated payload: %s", pipeline.current_result.payload)
            if not sender.is_open:
                now = time.monotonic()
                if (now - last_reconnect_attempt) < args.reconnect_interval:
                    continue
                last_reconnect_attempt = now

            _safe_send(sender, pipeline.current_result.payload, logger)
    finally:
        sender.close()
        pipeline.camera.close()


if __name__ == "__main__":
    main()
