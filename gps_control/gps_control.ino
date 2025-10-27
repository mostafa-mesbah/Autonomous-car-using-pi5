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
char currentMission = 's'; // Default: stop
String commandBuffer = "";
bool gpsDebugMode = false;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPSBaud);

  pinMode(pwm_1, OUTPUT);
  pinMode(pwm_2, OUTPUT);
  pinMode(dir_1, OUTPUT);
  pinMode(dir_2, OUTPUT);

  Serial.println(TinyGPSPlus::libraryVersion());
  Serial.println("Ready for commands: f, b, s, l, r, rl, rr, speed=<value>, g");
}

void loop() {
  // === Read serial commands ===
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      handleCommand(commandBuffer);
      commandBuffer = "";
    } else {
      commandBuffer += c;
    }
  }

  // === GPS data (optional) ===
  while (gpsSerial.available() > 0)
    gps.encode(gpsSerial.read());
}

// === COMMAND HANDLER ===
void handleCommand(String command) {
  command.trim();

  // Speed command
  if (command.startsWith("speed=")) {
    int newSpeed = command.substring(6).toInt();
    setSpeed(newSpeed);
    return;
  }

  // GPS toggle
  if (command == "g") {
    toggleGpsMode();
    return;
  }

  // Movement commands
  if (command == "f") moveForward();
  else if (command == "b") moveBackward();
  else if (command == "s") stopCar();
  else if (command == "rl") rollLeft();
  else if (command == "rr") rollRight();
  else if (command == "l") turnLeft();
  else if (command == "r") turnRight();
  else {
    Serial.print("unknown command: ");
    Serial.println(command);
    Serial.println("valid: f,b,s,l,r,rl,rr,speed=<value>,g");
  }
}

// === MOVEMENT FUNCTIONS ===
void moveForward() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'f';
  Serial.println("forward");
}

void moveBackward() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, LOW);
  digitalWrite(dir_2, LOW);
  currentMission = 'b';
  Serial.println("backward");
}

void rollRight() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, LOW);
  digitalWrite(dir_2, HIGH);
  currentMission = 'y'; // unique ID for roll right
  Serial.println("roll right");
}

void rollLeft() {
  analogWrite(pwm_1, currentSpeed);
  analogWrite(pwm_2, currentSpeed);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, LOW);
  currentMission = 'x'; // unique ID for roll left
  Serial.println("roll left");
}

void turnLeft() {
  analogWrite(pwm_1, 255);
  analogWrite(pwm_2, 80);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'l';
  Serial.println("turn left");
}

void turnRight() {
  analogWrite(pwm_1, 80);
  analogWrite(pwm_2, 255);
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, HIGH);
  currentMission = 'r';
  Serial.println("turn right");
}

void stopCar() {
  analogWrite(pwm_1, 0);
  analogWrite(pwm_2, 0);
  currentMission = 's';
  Serial.println("stop");
}

// === GPS MODE ===
void toggleGpsMode() {
  gpsDebugMode = !gpsDebugMode;
  Serial.print("gps mode: ");
  Serial.println(gpsDebugMode ? "detailed" : "simple");
}

// === SPEED CONTROL ===
void setSpeed(int newSpeed) {
  currentSpeed = constrain(newSpeed, minSpeed, maxSpeed);
  Serial.print("speed set to: ");
  Serial.println(currentSpeed);
  applyCurrentMission();
}

// === APPLY LAST COMMAND ===
void applyCurrentMission() {
  if (currentMission == 'f') moveForward();
  else if (currentMission == 'b') moveBackward();
  else if (currentMission == 'r') turnRight();
  else if (currentMission == 'l') turnLeft();
  else if (currentMission == 'x') rollLeft();
  else if (currentMission == 'y') rollRight();
  else if (currentMission == 's') stopCar();
}
