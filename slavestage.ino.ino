#include <Servo.h>

Servo doorServo;
Servo windowServo;

#define BUTTON_PIN 2

void setup() {
  Serial.begin(9600);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  doorServo.attach(9);
  windowServo.attach(10);

  doorServo.write(0);    // porte fermée
  windowServo.write(0);  // fenêtre fermée
}

void loop() {

  // 🔔 Sonnette
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("BELL");
    delay(1000); // anti-rebond
  }

  // 📩 Commandes ESP32
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');

    // 🚪 PORTE
    if (cmd == "OPEN_DOOR") {
      doorServo.write(90);
      delay(40000);
      doorServo.write(0);
    }

    if (cmd == "KEEP_OPEN_DOOR") {
      doorServo.write(90);
    }

    if (cmd == "CLOSE_DOOR") {
      doorServo.write(0);
    }

    // 🪟 FENÊTRE
    if (cmd == "OPEN_WINDOW") {
      windowServo.write(90);
    }

    if (cmd == "CLOSE_WINDOW") {
      windowServo.write(0);
    }
  }
}