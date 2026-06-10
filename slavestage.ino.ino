#include <Servo.h>

Servo doorServo;
Servo windowServo;

#define BUTTON_PIN 2
#define LED_PIN 11

unsigned long porteChrono = 0;
bool porteEnAttenteFermeture = false;

void setup() {
  Serial.begin(9600);

  pinMode(BUTTON_PIN, INPUT_PULLUP); 
  pinMode(LED_PIN, OUTPUT);

  doorServo.attach(9);
  windowServo.attach(10);

  doorServo.write(0);   
  windowServo.write(0);  
  digitalWrite(LED_PIN, LOW);
}

void loop() {

  // 🔔 Détection Sonnette
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("SNAP_PHOTO"); // Transmis à l'ESP32, qui le publiera en MQTT
    delay(1000); // Anti-rebond
  }

  // 📩 Réception des ordres de l'ESP32 (via messages convertis du MQTT)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    // Actionneur PORTE
    if (cmd == "OPEN_DOOR") {
      doorServo.write(90);
      porteChrono = millis();
      porteEnAttenteFermeture = true;
    }
    if (cmd == "KEEP_OPEN_DOOR") {
      doorServo.write(90);
      porteEnAttenteFermeture = false;
    }
    if (cmd == "CLOSE_DOOR") {
      doorServo.write(0);
      porteEnAttenteFermeture = false;
    }

    // Actionneur FENÊTRE
    if (cmd == "OPEN_WINDOW") {
      windowServo.write(90);
    }
    if (cmd == "CLOSE_WINDOW") {
      windowServo.write(0);
    }

    // Actionneur LUMIÈRE
    if (cmd == "TURN_ON_LED") {
      digitalWrite(LED_PIN, HIGH);
    }
    if (cmd == "TURN_OFF_LED") {
      digitalWrite(LED_PIN, LOW);
    }
  }

  // Minuteur automatique pour la porte (40 secondes)
  if (porteEnAttenteFermeture && (millis() - porteChrono >= 40000)) {
    doorServo.write(0);
    porteEnAttenteFermeture = false;
  }
}
