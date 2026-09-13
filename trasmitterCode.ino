#include <SPI.h>
#include <LoRa.h>

#define SS    5
#define RST   14
#define DIO0  2

void setup() {
  Serial.begin(115200);

  LoRa.setPins(SS, RST, DIO0);

  if (!LoRa.begin(433E6)) {
    while (1);
  }
}

void loop() {

  if (Serial.available()) {

    // Receive the complete string from Raspberry Pi
    String data = Serial.readStringUntil('\n');

    data.trim();

    if (data.length() > 0 && data.length() <= 253) {

      // Send the complete string as ONE LoRa packet
      LoRa.beginPacket();
      LoRa.print(data);
      LoRa.endPacket();
    }
  }
}
