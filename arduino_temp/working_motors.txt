#include <SparkFun_TB6612.h>

// ---------- Pin definitions ----------
// Front driver
#define F_PWMA 7
#define F_AIN2 34
#define F_AIN1 36
#define F_STBY 38
#define F_BIN1 40
#define F_BIN2 42
#define F_PWMB 6

// Back driver
#define B_PWMA 5
#define B_AIN1 35
#define B_AIN2 33
#define B_STBY 37
#define B_BIN1 39
#define B_BIN2 41
#define B_PWMB 4

// IR
#define left_IR_analog A0
#define left_IR_digital 42   // NOTE: same pin as F_BIN2 (42) - one of them needs to move

#define right_IR_analog A1
#define right_IR_digital 43

// Direction offsets: use 1 normally, or -1 to flip a motor's direction
const int OFFSET_FL = -1;
const int OFFSET_FR = 1;
const int OFFSET_BL = -1;
const int OFFSET_BR = 1;

// ---------- Settings ----------
const int DEFAULT_SPEED_PCT = 60;       // 0-100 %, used when no speed is given (e.g. "W_1")
const float MAX_DURATION_S = 30.0;      // safety cap on a single command
const unsigned int MAX_CMD_LEN = 32;    // guard against runaway input

// ---------- Test settings ----------
const int TEST_SPEED = 150;     // 0-255
const int RUN_TIME_MS = 1500;   // how long each direction runs
const int PAUSE_MS = 500;       // pause between steps

// ---------- Motors ----------
Motor frontLeft   = Motor(B_AIN1, B_AIN2, B_PWMA, OFFSET_FL, B_STBY);
Motor frontRight  = Motor(B_BIN1, B_BIN2, B_PWMB, OFFSET_FR, B_STBY);
Motor backLeft    = Motor(F_BIN1, F_BIN2, F_PWMB, OFFSET_BL, F_STBY);
Motor backRight   = Motor(F_AIN1, F_AIN2, F_PWMA, OFFSET_BR, F_STBY);

// ---------- State ----------
bool moving = false;
unsigned long moveStartMs = 0;
unsigned long moveDurationMs = 0;

String inputBuffer = "";

// ---------- Motion primitives ----------
void setMotors(int fl, int fr, int bl, int br) {
  frontLeft.drive(fl);
  frontRight.drive(fr);
  backLeft.drive(bl);
  backRight.drive(br);
}

void stopAllMotors() {
  frontLeft.brake();
  frontRight.brake();
  backLeft.brake();
  backRight.brake();
}

void forward(int s)        { setMotors( s,  s,  s,  s); }
void backward(int s)       { setMotors(-s, -s, -s, -s); }
void strafeLeft(int s)     { setMotors(-s,  s,  s, -s); }
void strafeRight(int s)    { setMotors( s, -s, -s,  s); }
void rotateCCW(int s)      { setMotors(-s,  s, -s,  s); }  // left side back, right side forward
void rotateCW(int s)       { setMotors( s, -s,  s, -s); }  // left side forward, right side back

// ---------- Startup motor test (blocking - not interruptible) ----------
void testOneMotor(const char *name, Motor &m) {
  Serial.print(name);
  Serial.println(" forward");
  m.drive(TEST_SPEED);
  delay(RUN_TIME_MS);
  m.brake();
  delay(PAUSE_MS);

  Serial.print(name);
  Serial.println(" backward");
  m.drive(-TEST_SPEED);
  delay(RUN_TIME_MS);
  m.brake();
  delay(PAUSE_MS);
}

void testMotors() {
  testOneMotor("front left",  frontLeft);
  testOneMotor("front right", frontRight);
  testOneMotor("back left",   backLeft);
  testOneMotor("back right",  backRight);
  Serial.println("Motor test complete");
}

void runStartupTest() {
  testMotors();

  Serial.println("all motors forward");
  forward(TEST_SPEED);
  delay(2000);

  Serial.println("all motors backward");
  backward(TEST_SPEED);
  delay(2000);

  stopAllMotors();
}

// ---------- Command handling ----------
// Command format: <letter>_<seconds>_<speed percent 1-100>
//   e.g. Q_0.5_50   rotate CCW for 0.5 s at 50% speed
//        W_2_80     forward for 2 s at 80% speed
//        W_2        forward for 2 s at DEFAULT_SPEED_PCT
//
//   W forward   S backward   A left   D right
//   Q rotate counterclockwise   E rotate clockwise
//   X stop immediately (works instantly, no Enter needed)
//
// Sending any new valid command while one is running replaces it immediately.

void stopNow() {
  stopAllMotors();
  moving = false;
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  if (cmd.length() == 0) return;

  char dir = cmd.charAt(0);

  if (dir == 'X') {
    stopNow();
    Serial.println("Stopped");
    return;
  }

  // Split into letter / seconds / speed on '_'
  int first = cmd.indexOf('_');
  if (first != 1) {
    Serial.println("Error: format is <letter>_<seconds>_<speed> (example: Q_0.5_50)");
    return;
  }

  int second = cmd.indexOf('_', first + 1);
  String durStr, spdStr;
  if (second == -1) {
    durStr = cmd.substring(first + 1);
    spdStr = "";
  } else {
    durStr = cmd.substring(first + 1, second);
    spdStr = cmd.substring(second + 1);
  }

  float seconds = durStr.toFloat();
  if (seconds <= 0) {
    Serial.println("Error: invalid duration");
    return;
  }
  if (seconds > MAX_DURATION_S) {
    seconds = MAX_DURATION_S;
    Serial.println("Duration capped at max");
  }

  int percent = DEFAULT_SPEED_PCT;
  if (spdStr.length() > 0) {
    percent = spdStr.toInt();
    if (percent <= 0) {
      Serial.println("Error: invalid speed (use 1-100 %)");
      return;
    }
    if (percent > 100) {
      percent = 100;
      Serial.println("Speed capped at 100%");
    }
  }
  int speed = (percent * 255 + 50) / 100;   // convert % to 0-255 PWM, rounded

  // Validate direction before touching the motors, so a bad command
  // doesn't disturb a move that's already in progress.
  const char *label;
  switch (dir) {
    case 'W': label = "Forward";    break;
    case 'S': label = "Backward";   break;
    case 'A': label = "Left";       break;
    case 'D': label = "Right";      break;
    case 'Q': label = "Rotate CCW"; break;
    case 'E': label = "Rotate CW";  break;
    default:
      Serial.print("Error: unknown command '");
      Serial.print(dir);
      Serial.println("'");
      return;
  }

  // Valid command: this replaces any move currently in progress
  switch (dir) {
    case 'W': forward(speed);     break;
    case 'S': backward(speed);    break;
    case 'A': strafeLeft(speed);  break;
    case 'D': strafeRight(speed); break;
    case 'Q': rotateCCW(speed);   break;
    case 'E': rotateCW(speed);    break;
  }

  Serial.print(label);
  Serial.print(" ");
  Serial.print(seconds, 2);
  Serial.print(" s @ ");
  Serial.print(percent);
  Serial.println("%");

  moveStartMs = millis();
  moveDurationMs = (unsigned long)(seconds * 1000.0);
  moving = true;
}

void readSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    // Instant stop: a lone X/x stops the motors right away,
    // without waiting for a newline.
    if ((c == 'X' || c == 'x') && inputBuffer.length() == 0) {
      stopNow();
      Serial.println("Stopped");
      continue;
    }

    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        handleCommand(inputBuffer);
        inputBuffer = "";
      }
    } else if (inputBuffer.length() < MAX_CMD_LEN) {
      inputBuffer += c;
    } else {
      // Overlong garbage: drop it
      inputBuffer = "";
      Serial.println("Error: command too long");
    }
  }
}

// ---------- Setup / loop ----------
void setup() {
  Serial.begin(9600);
  delay(1000);

  // runStartupTest();   // blocking - cannot be interrupted, leave disabled for normal use

  while (Serial.available() > 0) Serial.read();
  inputBuffer = "";

  Serial.println("Ready. Format: <W/S/A/D/Q/E>_<seconds>_<speed 1-100 %>  (e.g. Q_0.5_50). X = stop.");
}

void loop() {
  readSerial();   // always polled, so commands can arrive at any time

  if (moving && (millis() - moveStartMs >= moveDurationMs)) {
    stopNow();
    Serial.println("Done");
  }
}