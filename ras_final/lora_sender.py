"""Serial transport for compact SAR JSON telemetry."""

from __future__ import annotations

import serial

from .payload import ensure_within_limit


class LoRaSender:
    """Send one documented JSON payload per newline-delimited UART record."""

    def __init__(self, port: str, baudrate: int = 115200, timeout_seconds: float = 2.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout_seconds = timeout_seconds
        self._serial: serial.Serial | None = None

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def open(self) -> None:
        if not self.is_open:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout_seconds)

    def close(self) -> None:
        if self.is_open:
            assert self._serial is not None
            self._serial.close()

    def send_text(self, payload: str) -> None:
        """Transmit validated compact JSON without alternate framing formats."""
        ensure_within_limit(payload)
        self.open()
        assert self._serial is not None
        packet = payload.encode("utf-8") + b"\n"
        written = self._serial.write(packet)
        if written != len(packet):
            raise IOError(f"serial write incomplete: {written}/{len(packet)} bytes")
