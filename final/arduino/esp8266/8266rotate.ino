#include <Servo.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "Bettet";
const char* password = "pwd12345";

ESP8266WebServer server(80);

Servo servo1, servo2;
int servo1Pin = 4;  // GPIO for first servo d2
int servo2Pin = 5;  // GPIO for second servo d1

int angle1 = 90, angle2 = 90; // Initial angles
int step = 3;
unsigned long previousMillis = 0;
const long interval = 50; 

bool rotatingLeft1 = false, rotatingRight1 = false;
bool rotatingLeft2 = false, rotatingRight2 = false;

void rotateLeft1() {
  rotatingLeft1 = true;
  rotatingRight1 = false;
  server.send(200, "text/plain", "Servo 1 Rotating Left");
}

void rotateRight1() {
  rotatingRight1 = true;
  rotatingLeft1 = false;
  server.send(200, "text/plain", "Servo 1 Rotating Right");
}

void stopRotation1() {
  rotatingLeft1 = false;
  rotatingRight1 = false;
  server.send(200, "text/plain", "Servo 1 Stopped");
}

void rotateLeft2() {
  rotatingLeft2 = true;
  rotatingRight2 = false;
  server.send(200, "text/plain", "Servo 2 Rotating Left");
}

void rotateRight2() {
  rotatingRight2 = true;
  rotatingLeft2 = false;
  server.send(200, "text/plain", "Servo 2 Rotating Right");
}

void stopRotation2() {
  rotatingLeft2 = false;
  rotatingRight2 = false;
  server.send(200, "text/plain", "Servo 2 Stopped");
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to Wi-Fi...");
  }
  Serial.println("Connected to Wi-Fi");
  Serial.println(WiFi.localIP());

  servo1.attach(servo1Pin, 500, 2400);
  servo2.attach(servo2Pin, 500, 2400);

  servo1.write(angle1);
  servo2.write(angle2);

  server.on("/servo1/left", rotateLeft1);
  server.on("/servo1/right", rotateRight1);
  server.on("/servo1/stop", stopRotation1);

  server.on("/servo2/left", rotateLeft2);
  server.on("/servo2/right", rotateRight2);
  server.on("/servo2/stop", stopRotation2);

  server.begin();
}

void loop() {
  server.handleClient();
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    if (rotatingLeft1 && angle1 > 0) {
      angle1 -= step;
      if (angle1 < 0) angle1 = 0;
      servo1.write(angle1);
    } else if (rotatingRight1 && angle1 < 180) {
      angle1 += step;
      if (angle1 > 180) angle1 = 180;
      servo1.write(angle1);
    }

    if (rotatingLeft2 && angle2 > 0) {
      angle2 -= step;
      if (angle2 < 0) angle2 = 0;
      servo2.write(angle2);
    } else if (rotatingRight2 && angle2 < 180) {
      angle2 += step;
      if (angle2 > 180) angle2 = 180;
      servo2.write(angle2);
    }
  }
}
