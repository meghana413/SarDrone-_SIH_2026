"""Reference LoRa sender for an alternative compact SAR payload.

This is not the live protocol used by ``ras_final.main``. The active Raspberry Pi
runtime serializes telemetry with ``protocol.serialize_result()`` as
``[[persons],[path]]|CONFIDENCE`` and sends that via UART to the ESP32.
"""
    
from __future__ import annotations

import json
import struct
import zlib
from typing import Any, Mapping

import serial

MAGIC = b"SAR1"
_HEADER = struct.Struct("!4sH")
_CRC = struct.Struct("!I")


class LoRaSender:
    def __init__(self, port: str, baudrate: int = 115200, timeout_seconds: float = 1.0, max_packet_bytes: int = 512) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout_seconds = timeout_seconds
        self.max_packet_bytes = max_packet_bytes
        self._serial: serial.Serial | None = None

    def open(self) -> None:
        if self._serial is None or not self._serial.is_open:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout_seconds)

    def close(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()

    def encode(self, payload: Mapping[str, Any]) -> bytes:
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(body) > self.max_packet_bytes:
            raise ValueError(f"payload length {len(body)} exceeds {self.max_packet_bytes} bytes")
        return _HEADER.pack(MAGIC, len(body)) + body + _CRC.pack(zlib.crc32(body) & 0xFFFFFFFF)

    def send(self, payload: Mapping[str, Any]) -> None:
        self.open()
        assert self._serial is not None
        packet = self.encode(payload)
        written = self._serial.write(packet)
        if written != len(packet):
            raise IOError(f"serial write incomplete: {written}/{len(packet)} bytes")

    def send_compact_text(self, text: str, suffix: bytes = b"_") -> None:
        self.open()
        assert self._serial is not None
        packet = text.encode("ascii") + suffix
        written = self._serial.write(packet)
        if written != len(packet):
            raise IOError(f"serial write incomplete: {written}/{len(packet)} bytes")


if __name__ == "__main__":
    sender = LoRaSender("/dev/ttyUSB0")
    sample = {"v": [[120, 200], [130, 210]], "p": [[0, 0], [1, 0], [2, 1]]}
    sender.send(sample)
    print("payload sent")
