#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include "Adafruit_MPRLS.h"

// You dont *need* a reset and EOC pin for most uses, so we set to -1 and don't connect
#define RESET_PIN  -1  // set to any GPIO pin # to hard-reset on begin()
#define EOC_PIN    -1  // set to any GPIO pin to read end-of-conversion by pin
Adafruit_MPRLS mpr = Adafruit_MPRLS(RESET_PIN, EOC_PIN);

const char* ssid = "POCO F3";
const char* password = "1234560000";
const char* mqtt_server = "192.168.86.230";
const char* mqtt_topic = "L2_R2"; //robot2
const char* mqtt_ID = "ESP-client2";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long previousMillis = 0; // Variable para almacenar el tiempo transcurrido
const long interval = 400; // Intervalo de tiempo en milisegundos

void setup() {
  Serial.begin(115200);
  mpr.begin();

  delay(15000); 
  // conectarse al wifi
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando a la red WiFi...");
  }

  // conexion MQTT
  client.setServer(mqtt_server, 1883);
  client.connect("mqtt_ID"); //id del segundo robot
}

void loop() {
  client.loop();

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    float pressure_hPa = mpr.readPressure();
    Serial.print("Pressure (hPa): "); Serial.println(pressure_hPa);
    Serial.print("Pressure (PSI): "); Serial.println(pressure_hPa / 68.947572932);

    bool published = false;  // Variable para verificar si se publicó correctamente el mensaje MQTT

// Envío del valor de la presión por MQTT
char message[10];
sprintf(message, "%.2f", pressure_hPa);
if (client.publish(mqtt_topic, message)) {
  published = true;
  Serial.println("Publicar ok");
} else {
  published = false;
}

// Verificación del estado de publicación y mensaje correspondiente
if (published) {
  Serial.println("El mensaje se publicó correctamente");
} else {
  Serial.println("Error al publicar el mensaje");
}
  }
}
