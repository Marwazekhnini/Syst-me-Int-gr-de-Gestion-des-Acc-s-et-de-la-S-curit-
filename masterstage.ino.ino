#include <WiFi.h>
#include <WebServer.h>

WebServer server(80);

void openDoor() {
  Serial.println("OPEN"); // envoyer à Arduino
  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(9600);

  WiFi.begin("SSID", "PASS");
  while (WiFi.status() != WL_CONNECTED) {}

  server.on("/open", openDoor);
  server.begin();
}

void loop() {
  server.handleClient();
}