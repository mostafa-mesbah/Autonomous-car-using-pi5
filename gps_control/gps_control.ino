#include <TinyGPS++.h>
#include <SoftwareSerial.h>

// === GPS Pins ===
#define RXPin 3    // GPS RX
#define TXPin 4    // GPS TX
#define GPSBaud 9600

// === Motor Pins ===
#define pwm_1 5
#define pwm_2 6
#define dir_1 7 // left motor
#define dir_2 8 // right motor

// === GPS Setup ===
TinyGPSPlus gps;
SoftwareSerial gpsSerial(RXPin, TXPin);

// === Speed Variables ===
int currentSpeed = 150;
int maxSpeed = 255;
int minSpeed = 0;

// === Mission Variables ===
char currentMission = 'S'; // Default: Stop
String commandBuffer = "";
unsigned long lastGpsSend = 0;
bool gpsDebugMode = false;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPSBaud);

  pinMode(pwm_1, OUTPUT);
  pinMode(pwm_2, OUTPUT);
  pinMode(dir_1, OUTPUT);
  pinMode(dir_2, OUTPUT);

  Serial.println(TinyGPSPlus::libraryVersion());
}

void loop() {
  // Handle commands from Raspberry Pi
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      handleCommand(commandBuffer);
      commandBuffer = "";
    } else {
      commandBuffer += c;
    }
  }
}

// === COMMAND HANDLER ===
void handleCommand(String command) {

  // Speed command
  if (command.startsWith("speed=")) {
    int newSpeed = command.substring(6).toInt();
    setSpeed(newSpeed);
    return;
  }

  // Movement commands (lowercase)
  if (command == "f") moveForward();
  else if (command == "b") moveBackward();
  else if (command == "s") stopCar();
  else if (command == "rl") RollLeft();
  else if (command == "l") TurnLeft();
  else if (command == "rr") RollRight();
  else if (command == "r") TurnRight();

  // Single-character legacy commands
  else if (command.length() == 1) {
    char cmd = command.charAt(0);
    switch (cmd) {
      case 'F': moveForward(); break;
      case 'B': moveBackward(); break;
      case 'R': RollRight(); break;
      case 'L': RollLeft(); break;
      case 'S': stopCar(); break;
      case 'G': toggleGpsMode(); break;
      default:
        Serial.print(F("Unknown command: "));
        Serial.println(cmd);
        Serial.println(F("Valid commands: F,B,R,L,S,G,speed=<value>,f,b,s,l,rl,r,rr"));
        break;
    }
  } else {
    Serial.print(F("Unknown command: "));
    Serial.println(command);
  }
}

// === MOVEMENT FUNCTIONS ===
void moveForward() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'F';
  Serial.println(F("FORWARD"));
}

void moveBackward() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, LOW);
  digitalWrite(dir_2, LOW);
  currentMission = 'B';
  Serial.println(F("BACKWARD"));
}

void RollRight() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, LOW);
  digitalWrite(dir_2, HIGH);
  currentMission = 'R';
  Serial.println(F("ROLL RIGHT"));
}

void RollLeft() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, LOW);
  currentMission = 'L';
  Serial.println(F("ROLL LEFT"));
}

void TurnLeft() {
  analogWrite(pwm_1, 255);   // Left motor full
  analogWrite(pwm_2, 80);    // Right motor slow
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'l';
  Serial.println(F("TURN LEFT"));
}

void TurnRight() {
  analogWrite(pwm_1, 80);    // Left motor slow
  analogWrite(pwm_2, 255);   // Right motor full
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'r';
  Serial.println(F("TURN RIGHT"));
}

void stopCar() {
  analogWrite(pwm_1, 0);
  analogWrite(pwm_2, 0);
  currentMission = 'S';
  Serial.println(F("STOP"));
}

// === GPS MODE ===
void toggleGpsMode() {
  gpsDebugMode = !gpsDebugMode;
  Serial.print(F("GPS Mode: "));
  Serial.println(gpsDebugMode ? F("DETAILED") : F("SIMPLE"));
}

// === GPS DATA OUTPUT ===
void sendSimpleGpsData() {
  if (gps.location.isValid()) {
    Serial.print(F("GPS,"));
    Serial.print(gps.location.lat(), 10);
    Serial.print(F(","));
    Serial.print(gps.location.lng(), 10);
    Serial.print(F(","));
    Serial.println(gps.satellites.isValid() ? gps.satellites.value() : 0);
  } else {
    Serial.println(F("GPS,INVALID,INVALID,0"));
  }
}

void sendDetailedGpsData() {
  Serial.println(F("=== GPS DETAILS ==="));

  if (gps.location.isValid()) {
    Serial.print(F("Location: "));
    Serial.print(gps.location.lat(), 10);
    Serial.print(F(", "));
    Serial.print(gps.location.lng(), 10);
    Serial.print(F(" Alt: "));
    Serial.println(gps.altitude.isValid() ? gps.altitude.meters() : 0);
  } else {
    Serial.println(F("Location: INVALID"));
  }

  Serial.print(F("Date/Time: "));
  if (gps.date.isValid()) {
    Serial.print(gps.date.day());
    Serial.print("/");
    Serial.print(gps.date.month());
    Serial.print("/");
    Serial.print(gps.date.year());
  } else Serial.print(F("INVALID"));

  Serial.print(" ");
  if (gps.time.isValid()) {
    if (gps.time.hour() < 10) Serial.print("0");
    Serial.print(gps.time.hour());
    Serial.print(":");
    if (gps.time.minute() < 10) Serial.print("0");
    Serial.print(gps.time.minute());
    Serial.print(":");
    if (gps.time.second() < 10) Serial.print("0");
    Serial.println(gps.time.second());
  } else Serial.println(F("INVALID"));

  Serial.print(F("Sats: "));
  Serial.println(gps.satellites.isValid() ? gps.satellites.value() : 0);
}

void applyCurrentMission() {
  switch (currentMission) {
    case 'F': moveForward(); break;
    case 'B': moveBackward(); break;
    case 'R': RollRight(); break;
    case 'L': RollLeft(); break;
    case 'S': stopCar(); break;
  }
}

// === SPEED CONTROL ===
void setSpeed(int newSpeed) {
  currentSpeed = constrain(newSpeed, minSpeed, maxSpeed);
  Serial.print(F("Speed set to: "));
  Serial.println(currentSpeed);
  applyCurrentMission(); // Apply the new speed
}
