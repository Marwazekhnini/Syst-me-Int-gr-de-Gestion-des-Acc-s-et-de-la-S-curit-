#include <WiFi.h>
#include <PubSubClient.h>


// 🌐 Configurations Wi-Fi
const char* ssid = "Fibre_MarocTelecom_5G";
const char* password = "TQxTD2PN";

// 🌐 Configuration MQTT (Mettre l'IP de la machine Node-RED)
const char* mqtt_server = "127.0.0.1"; // <── REMPLACE PAR L'IP DE NODE-RED
const int mqtt_port = 1880;

WiFiClient espClient;
PubSubClient client(espClient);

// Fonction de réception des messages MQTT (Node-RED -> ESP32)
void callback(char* topic, byte* payload, unsigned long length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  // On convertit les topics et payloads pour l'Arduino (Slave)
  String topicStr = String(topic);

  if (topicStr == "security/door/command") {
    if (message == "/open") Serial.println("OPEN_DOOR");
    else if (message == "/keep_open") Serial.println("KEEP_OPEN_DOOR");
    else if (message == "/close") Serial.println("CLOSE_DOOR");
  } 
  else if (topicStr == "security/insidebooth/window/command") {
    if (message == "/open_window") Serial.println("OPEN_WINDOW");
    else if (message == "/close_window") Serial.println("CLOSE_WINDOW");
  } 
  else if (topicStr == "security/insidebooth/light/command") {
    if (message == "/ON") Serial.println("TURN_ON_LED");
    else if (message == "/OFF") Serial.println("TURN_OFF_LED");
  }
}

// Reconnexion automatique au Broker MQTT
void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Master")) {
      // Inscription aux topics définis dans ton Node-RED
      client.subscribe("security/door/command");
      client.subscribe("security/insidebooth/window/command");
      client.subscribe("security/insidebooth/light/command");
    } else {
      delay(5000);
    }
  }
}

void setup() {
  // Communication Série avec l'Arduino Uno
  Serial.begin(9600);

  // Connexion Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  // Configuration MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Écoute de l'Arduino (ex: bouton sonnette pressé)
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg == "SNAP_PHOTO") {
      // On publie sur le topic que ton Node-RED écoute pour la sonnette
      client.publish("security/camera/alert", "🔔 DOORBELL_PRESSED");
    }
  }
}
