#include <ESP8266WiFi.h>

const char* ssid = "mm";
const char* password = "1234568m";

WiFiServer server(80);

// GPIO pins for LEDs (D1,D2,D5,D6,D7)
int ledPins[] = {5, 4, 14, 12, 13};
int numLeds = 5;

// store LED states
bool ledState[5] = {0,0,0,0,0};

void setup() {

  Serial.begin(115200);

  // Setup LED pins
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  // Test LEDs
  Serial.println("Testing LEDs...");
  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(300);
    digitalWrite(ledPins[i], LOW);
  }

  // Connect WiFi
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi Connected");
  Serial.print("ESP8266 IP: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {

  WiFiClient client = server.available();

  if (client) {

    Serial.println("Client Connected");

    while (client.connected()) {

      if (client.available()) {

        String request = client.readStringUntil('\n');
        request.trim();

        Serial.println("Received: " + request);

        if (request.startsWith("FINGERS:")) {

          int fingerCount = request.substring(8).toInt();
          controlFingerLEDs(fingerCount);

          client.println("OK");
        }

        else if (request == "CLEAR") {

          turnOffAllLEDs();
          client.println("CLEARED");
        }

        else if (request == "TEST") {

          testAllLEDs();
          client.println("TESTED");
        }
      }
    }

    client.stop();
    Serial.println("Client disconnected");
  }
}

void controlFingerLEDs(int fingerCount) {

  fingerCount = constrain(fingerCount, 0, 5);

  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], LOW);
    ledState[i] = false;
  }

  if (fingerCount > 0) {

    digitalWrite(ledPins[fingerCount - 1], HIGH);
    ledState[fingerCount - 1] = true;
  }

  printLEDStatus();
}

void turnOffAllLEDs() {

  for (int i = 0; i < numLeds; i++) {
    digitalWrite(ledPins[i], LOW);
    ledState[i] = false;
  }

  printLEDStatus();
}

void testAllLEDs() {

  for (int i = 0; i < numLeds; i++) {

    digitalWrite(ledPins[i], HIGH);
    ledState[i] = true;

    printLEDStatus();

    delay(300);

    digitalWrite(ledPins[i], LOW);
    ledState[i] = false;
  }

  printLEDStatus();
}

void printLEDStatus() {

  Serial.println("------ LED STATUS ------");

  bool allOff = true;

  for (int i = 0; i < numLeds; i++) {

    Serial.print("LED");
    Serial.print(i + 1);
    Serial.print(": ");

    if (ledState[i]) {
      Serial.println("ON");
      allOff = false;
    }
    else {
      Serial.println("OFF");
    }
  }

  if (allOff) {
    Serial.println("ALL LEDs are OFF");
  }

  Serial.println("------------------------");
}