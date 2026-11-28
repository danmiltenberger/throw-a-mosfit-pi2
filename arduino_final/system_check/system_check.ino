/*
  Stepper + DC motor test with serial command control (Arduino Mega)
  Libraries: AccelStepper, SparkFun TB6612FNG (SparkFun_TB6612.h)

  SERIAL COMMANDS (115200 baud, newline-terminated):
    <MOTOR>_<SPEED%>_<SECONDS>     e.g.  LF_100_10   left front, 100% speed, 10 s
                                         RB_-50_2.5  right back, 50% reverse, 2.5 s
    MOTOR: LF, RF, LB, RB, or ALL
    SPEED: -100 to 100 (negative = reverse)
    SECONDS: run time, decimals allowed

    STRAFE_<SPEED%>_<ANGLE>[_<SECONDS>]   mecanum drive (X roller layout)
        ANGLE is in degrees, +CCW from the robot's east (right):
          0 = right, 90 = forward, 180 = left, 270 = back
        e.g.  STRAFE_50_90      forward at 50% until STOP
              STRAFE_100_180_3  strafe left at 100% for 3 s
        SPEED % is the duty of the fastest wheel; the other wheels are scaled to match.

    STOP    brake all motors immediately
    TEST    run the full automatic motor test sequence

  Commands are non-blocking: each motor stops on its own timer.

  MOTOR MAPPING (edit motorNames[]/motors[] below if yours differs):
    Back driver  (Left-Back pins)   A = LB, B = RB
    Front driver (Right-Front pins) A = RF, B = LF

  IMPORTANT: for STRAFE to work, a POSITIVE speed must spin every wheel
  "forward" (robot moves forward). Set the per-motor offsets below so this is true.
*/

#include <AccelStepper.h>
#include <SparkFun_TB6612.h>

// ---------------- Stepper pins ----------------
#define L_STEP_EN   22
#define L_STEP_STEP 24
#define L_STEP_DIR  26

#define R_STEP_EN   23
#define R_STEP_STEP 25
#define R_STEP_DIR  27

AccelStepper stepperL(AccelStepper::DRIVER, L_STEP_STEP, L_STEP_DIR);
AccelStepper stepperR(AccelStepper::DRIVER, R_STEP_STEP, R_STEP_DIR);

// ---------------- DC motor pins ----------------
// Left (Back) driver
#define LB_PWMA 7
#define LB_AIN2 12
#define LB_AIN1 11
#define LB_STBY 10
#define LB_BIN1 9
#define LB_BIN2 8
#define LB_PWMB 6

// Right (Front) driver
#define RF_PWMA 5
#define RF_AIN2 44
#define RF_AIN1 46
#define RF_STBY 48
#define RF_BIN1 50
#define RF_BIN2 52
#define RF_PWMB 4

// Offset: set to -1 for any motor that spins the wrong way
const int LB_A_offset = 1;
const int LB_B_offset = 1;
const int RF_A_offset = -1;
const int RF_B_offset = 1;

//             In1      In2      PWM      Offset   STBY
Motor motorLB_A(LB_AIN1, LB_AIN2, LB_PWMA, LB_A_offset, LB_STBY);
Motor motorLB_B(LB_BIN1, LB_BIN2, LB_PWMB, LB_B_offset, LB_STBY);
Motor motorRF_A(RF_AIN1, RF_AIN2, RF_PWMA, RF_A_offset, RF_STBY);
Motor motorRF_B(RF_BIN1, RF_BIN2, RF_PWMB, RF_B_offset, RF_STBY);

// ---------------- Motor name lookup ----------------
const int NUM_MOTORS = 4;
const char *motorNames[NUM_MOTORS] = {"LB", "RB", "RF", "LF"};
Motor *motors[NUM_MOTORS] = {&motorLB_A, &motorLB_B, &motorRF_A, &motorRF_B};

bool motorActive[NUM_MOTORS]         = {false, false, false, false};
bool motorTimed[NUM_MOTORS]          = {false, false, false, false};  // false = run until STOP
unsigned long motorEndMs[NUM_MOTORS] = {0, 0, 0, 0};

// ---------------- Stepper helpers (not used in the test sequence) ----------------
void initSteppers() {
  stepperL.setEnablePin(L_STEP_EN);
  stepperR.setEnablePin(R_STEP_EN);
  // (directionInvert, stepInvert, enableInvert) -> enable is active LOW
  stepperL.setPinsInverted(false, false, true);
  stepperR.setPinsInverted(false, false, true);

  stepperL.setMaxSpeed(800);       // steps/sec
  stepperL.setAcceleration(400);   // steps/sec^2
  stepperR.setMaxSpeed(800);
  stepperR.setAcceleration(400);

  stepperL.disableOutputs();
  stepperR.disableOutputs();
}

void runStepperBlocking(AccelStepper &s, long steps) {
  s.move(steps);
  while (s.distanceToGo() != 0) {
    s.run();
  }
}

void testStepper(AccelStepper &s, const char *name, long steps) {
  Serial.print(F("Stepper "));
  Serial.print(name);
  Serial.println(F(": forward"));
  s.enableOutputs();
  runStepperBlocking(s, steps);
  delay(500);

  Serial.print(F("Stepper "));
  Serial.print(name);
  Serial.println(F(": reverse"));
  runStepperBlocking(s, -steps);
  delay(500);
  s.disableOutputs();
}

// ---------------- Non-blocking motor control ----------------
// Start motor idx at percent (-100..100). seconds <= 0 means run until stopped.
void startMotor(int idx, float percent, float seconds) {
  percent = constrain(percent, -100.0f, 100.0f);
  int speed = (int)(percent * 255.0f / 100.0f);

  motors[idx]->drive(speed);
  motorActive[idx] = true;
  motorTimed[idx] = (seconds > 0);
  if (motorTimed[idx]) {
    motorEndMs[idx] = millis() + (unsigned long)(seconds * 1000.0f);
  }

  Serial.print(F("Motor "));
  Serial.print(motorNames[idx]);
  Serial.print(F(": "));
  Serial.print(percent, 0);
  Serial.print(F("% "));
  if (motorTimed[idx]) {
    Serial.print(F("for "));
    Serial.print(seconds, 1);
    Serial.println(F(" s"));
  } else {
    Serial.println(F("until STOP"));
  }
}

void stopMotor(int idx) {
  motors[idx]->brake();
  motorActive[idx] = false;
}

void stopAllMotors() {
  for (int i = 0; i < NUM_MOTORS; i++) stopMotor(i);
}

// Call every loop(): stops any timed motor whose timer has expired
void updateMotorTimers() {
  unsigned long now = millis();
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (motorActive[i] && motorTimed[i] && (long)(now - motorEndMs[i]) >= 0) {
      stopMotor(i);
      Serial.print(F("Motor "));
      Serial.print(motorNames[i]);
      Serial.println(F(": done"));
    }
  }
}

// Returns motor index for a name, or -1 if not found
int findMotor(const char *name) {
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (strcmp(name, motorNames[i]) == 0) return i;
  }
  return -1;
}

// ---------------- Mecanum strafe ----------------
/*
  Mecanum wheels in an X layout (viewed from above, rollers form an X).
  Angle is +CCW from the robot's east: vx = cos(angle) is rightward,
  vy = sin(angle) is forward.

    LF =  vy + vx        RF =  vy - vx
    LB =  vy - vx        RB =  vy + vx

  Check: 90 deg (forward)  -> all wheels forward
         0 deg (right)     -> LF, RB forward; RF, LB backward
         180 deg (left)    -> LF, RB backward; RF, LB forward

  Wheel values are scaled so the fastest wheel runs at speedPct.
  seconds <= 0 means run until STOP.
*/
void strafe(float speedPct, float angleDeg, float seconds) {
  float rad = angleDeg * PI / 180.0f;
  float vx = cos(rad);
  float vy = sin(rad);

  float lf = vy + vx;
  float rf = vy - vx;
  float lb = vy - vx;
  float rb = vy + vx;

  // lf^2 + rf^2 = 2, so the largest magnitude is always >= 1 (no divide by zero)
  float maxMag = max(fabs(lf), fabs(rf));
  float scale = speedPct / maxMag;

  Serial.print(F("STRAFE angle "));
  Serial.print(angleDeg, 1);
  Serial.print(F(" deg, speed "));
  Serial.print(speedPct, 0);
  Serial.println(F("%"));

  startMotor(findMotor("LF"), lf * scale, seconds);
  startMotor(findMotor("RF"), rf * scale, seconds);
  startMotor(findMotor("LB"), lb * scale, seconds);
  startMotor(findMotor("RB"), rb * scale, seconds);
}

// ---------------- Automatic test sequence (blocking) ----------------
void testMotor(Motor &m, const char *name, int speed = 150, int ms = 1000) {
  Serial.print(F("Motor "));
  Serial.print(name);
  Serial.println(F(": forward"));
  m.drive(speed, ms);
  m.brake();
  delay(300);

  Serial.print(F("Motor "));
  Serial.print(name);
  Serial.println(F(": reverse"));
  m.drive(-speed, ms);
  m.brake();
  delay(300);
}

void testAllMotors(int speed = 150, int ms = 1500) {
  Serial.println(F("All motors: forward"));
  for (int i = 0; i < NUM_MOTORS; i++) motors[i]->drive(speed);
  delay(ms);
  stopAllMotors();
  delay(500);

  Serial.println(F("All motors: reverse"));
  for (int i = 0; i < NUM_MOTORS; i++) motors[i]->drive(-speed);
  delay(ms);
  stopAllMotors();
  delay(500);
}

void testSteppersAndMotors() {
  // Stepper test skipped. Uncomment to re-enable:
  // testStepper(stepperL, "Left", 400);
  // testStepper(stepperR, "Right", 400);

  Serial.println(F("=== Testing DC motors individually ==="));
  for (int i = 0; i < NUM_MOTORS; i++) testMotor(*motors[i], motorNames[i]);

  Serial.println(F("=== Testing all DC motors together ==="));
  testAllMotors();

  Serial.println(F("=== Test complete ==="));
}

// ---------------- Serial command parser ----------------
void handleCommand(char *cmd) {
  // Uppercase
  for (char *p = cmd; *p; p++) *p = toupper(*p);

  if (strcmp(cmd, "STOP") == 0) {
    stopAllMotors();
    Serial.println(F("All motors stopped"));
    return;
  }
  if (strcmp(cmd, "TEST") == 0) {
    stopAllMotors();
    testSteppersAndMotors();
    return;
  }

  char *name = strtok(cmd, "_");
  char *tok1 = strtok(NULL, "_");
  char *tok2 = strtok(NULL, "_");
  char *tok3 = strtok(NULL, "_");   // only used by STRAFE (optional seconds)

  if (!name || !tok1) {
    Serial.println(F("Bad command. Use MOTOR_SPEED_SECONDS or STRAFE_SPEED_ANGLE"));
    return;
  }

  // ---- STRAFE_<speed>_<angle>[_<seconds>] ----
  if (strcmp(name, "STRAFE") == 0) {
    if (!tok2) {
      Serial.println(F("Bad command. Use STRAFE_SPEED_ANGLE[_SECONDS], e.g. STRAFE_50_90"));
      return;
    }
    float speedPct = atof(tok1);
    float angleDeg = atof(tok2);
    float seconds  = tok3 ? atof(tok3) : 0;   // 0 = until STOP
    strafe(speedPct, angleDeg, seconds);
    return;
  }

  // ---- <MOTOR>_<speed>_<seconds> ----
  if (!tok2) {
    Serial.println(F("Bad command. Use MOTOR_SPEED_SECONDS, e.g. LF_100_10"));
    return;
  }

  float speedPct = atof(tok1);
  float seconds  = atof(tok2);

  if (seconds <= 0) {
    Serial.println(F("Seconds must be greater than 0"));
    return;
  }

  if (strcmp(name, "ALL") == 0) {
    for (int i = 0; i < NUM_MOTORS; i++) startMotor(i, speedPct, seconds);
    return;
  }

  int idx = findMotor(name);
  if (idx < 0) {
    Serial.println(F("Unknown motor. Use LF, RF, LB, RB, ALL, or STRAFE"));
    return;
  }
  startMotor(idx, speedPct, seconds);
}

// Call every loop(): collects characters until newline, then runs the command
void readSerialCommands() {
  static char buf[32];
  static uint8_t len = 0;

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (len > 0) {
        buf[len] = '\0';
        handleCommand(buf);
        len = 0;
      }
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      len = 0;  // overflow: discard
      Serial.println(F("Command too long"));
    }
  }
}

void setup() {
  Serial.begin(115200);
  initSteppers();   // keeps stepper outputs disabled
  Serial.println(F("Ready. Commands: MOTOR_SPEED_SECONDS (LF_100_10), STRAFE_SPEED_ANGLE (STRAFE_50_90), STOP, TEST"));
}

void loop() {
  readSerialCommands();
  updateMotorTimers();
}
