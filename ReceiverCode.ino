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

  int packetSize = LoRa.parsePacket();

  if (packetSize > 0) {

    String data = "";

    // Receive the complete LoRa packet
    while (LoRa.available()) {
      data += (char)LoRa.read();
    }

    // Send the complete string to laptop
    Serial.println(data);
  }
}
