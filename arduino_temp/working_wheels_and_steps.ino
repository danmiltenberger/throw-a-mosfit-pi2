#include <AccelStepper.h>
#include <SparkFun_TB6612.h>

#define motorInterfaceType 1

// ---------- Steppers ----------
//                                      STEP DIR
AccelStepper stepper1(motorInterfaceType, 5, 4);  // LEFT stepper  (STEP 5, DIR 4)
AccelStepper stepper2(motorInterfaceType, 3, 2);  // RIGHT stepper (STEP 3, DIR 2)

// ---------- Motor driver BACK ----------
#define BACK_PWMA 12
#define BACK_AIN2 36
#define BACK_AIN1 38
#define BACK_BIN1 42
#define BACK_BIN2 44
#define BACK_PWMB 13

// ---------- Motor driver FRONT ----------
#define FRONT_PWMA 10
#define FRONT_AIN2 46
#define FRONT_AIN1 48
#define FRONT_BIN1 50
#define FRONT_BIN2 52
#define FRONT_PWMB 11

// ---------- Shared standby pin (both drivers) ----------
#define STBY 40

// Direction offsets: 1 = normal, -1 = reversed
const int offsetBackLeft   = 1;
const int offsetBackRight  = 1;
const int offsetFrontLeft  = 1;
const int offsetFrontRight = 1;

// Motor(In1, In2, PWM, offset, STBY)
Motor motorBackLeft   = Motor(BACK_AIN1,  BACK_AIN2,  BACK_PWMA,  offsetBackLeft,   STBY);  // back A
Motor motorBackRight  = Motor(BACK_BIN1,  BACK_BIN2,  BACK_PWMB,  offsetBackRight,  STBY);  // back B
Motor motorFrontLeft  = Motor(FRONT_AIN1, FRONT_AIN2, FRONT_PWMA, offsetFrontLeft,  STBY);  // front A
Motor motorFrontRight = Motor(FRONT_BIN1, FRONT_BIN2, FRONT_PWMB, offsetFrontRight, STBY);  // front B

// ---- Tune these for your hardware ----
const float STEPS_PER_REV = 200.0 * 1;  // 200 steps/rev x microstepping
const float MAX_SPEED     = 2000;       // steps/sec
const float ACCELERATION  = 8000;       // steps/sec^2
const int   DC_SPEED      = 200;        // 0-255 PWM duty for DC motors

// ---------- Stepper helpers ----------

long degreesToSteps(float degrees) {
  return round(degrees * STEPS_PER_REV / 360.0);
}

// Absolute move (non-blocking)
void moveToAngle(AccelStepper &stepper, float degrees) {
  stepper.moveTo(degreesToSteps(degrees));
}

// Relative move from a command like "STEPL_180_CCW" (non-blocking)
void startRotate(const String &command) {
  int sep1 = command.indexOf('_');
  int sep2 = command.indexOf('_', sep1 + 1);
  if (sep1 < 0 || sep2 < 0) {
    Serial.print("Invalid command: ");
    Serial.println(command);
    return;
  }

  String motorStr = command.substring(0, sep1);
  String degStr   = command.substring(sep1 + 1, sep2);
  String dirStr   = command.substring(sep2 + 1);

  motorStr.trim(); motorStr.toUpperCase();
  dirStr.trim();   dirStr.toUpperCase();

  AccelStepper *stepper;
  if (motorStr == "STEPL")      stepper = &stepper1;
  else if (motorStr == "STEPR") stepper = &stepper2;
  else {
    Serial.print("Invalid motor: ");
    Serial.println(motorStr);
    return;
  }

  long steps = degreesToSteps(degStr.toFloat());
  if (dirStr == "CCW")     steps = -steps;
  else if (dirStr != "CW") {
    Serial.print("Invalid direction: ");
    Serial.println(dirStr);
    return;
  }

  stepper->move(steps);
}

void runSteppers() {
  stepper1.run();
  stepper2.run();
}

bool steppersBusy() {
  return stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0;
}

// Blocks until both steppers finish their current moves
void waitForSteppers() {
  while (steppersBusy()) {
    runSteppers();
  }
}

// ---------- DC motor helpers (SparkFun TB6612 library) ----------

// speed: -255..255 (positive = forward, negative = backward)
// Spins one motor for durationMs milliseconds, then brakes. Blocking.
void spinMotor(Motor &motor, int speed, unsigned long durationMs) {
  motor.drive(speed);
  delay(durationMs);
  motor.brake();
}

// Spins all four DC motors together, then brakes them. Blocking.
void spinAllMotors(int speed, unsigned long durationMs) {
  motorBackLeft.drive(speed);
  motorBackRight.drive(speed);
  motorFrontLeft.drive(speed);
  motorFrontRight.drive(speed);
  delay(durationMs);
  motorBackLeft.brake();
  motorBackRight.brake();
  motorFrontLeft.brake();
  motorFrontRight.brake();
}

// ---------- Setup / Loop ----------

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }
  delay(1000);

  Serial.println("=== Motor test starting ===");

  // Stepper config
  stepper1.setMaxSpeed(MAX_SPEED);
  stepper1.setAcceleration(ACCELERATION);
  stepper2.setMaxSpeed(MAX_SPEED);
  stepper2.setAcceleration(ACCELERATION);
  // stepper2.setPinsInverted(true);  // uncomment if motors are mirrored

  // 1. Left stepper: 360 CW, then 360 CCW
  Serial.println("Step 1a: Left stepper 360 deg CW");
  startRotate("STEPL_360_CW");
  waitForSteppers();

  Serial.println("Step 1b: Left stepper 360 deg CCW");
  startRotate("STEPL_360_CCW");
  waitForSteppers();

  // 2. Right stepper: 360 CW, then 360 CCW
  Serial.println("Step 2a: Right stepper 360 deg CW");
  startRotate("STEPR_360_CW");
  waitForSteppers();

  Serial.println("Step 2b: Right stepper 360 deg CCW");
  startRotate("STEPR_360_CCW");
  waitForSteppers();

  // 3-6. BACK driver motors
  Serial.println("Step 3: Back left DC motor forward (2 sec)");
  spinMotor(motorBackLeft, DC_SPEED, 2000);

  Serial.println("Step 4: Back left DC motor backward (2 sec)");
  spinMotor(motorBackLeft, -DC_SPEED, 2000);

  Serial.println("Step 5: Back right DC motor forward (2 sec)");
  spinMotor(motorBackRight, DC_SPEED, 2000);

  Serial.println("Step 6: Back right DC motor backward (2 sec)");
  spinMotor(motorBackRight, -DC_SPEED, 2000);

  // 7-10. FRONT driver motors
  Serial.println("Step 7: Front left DC motor forward (2 sec)");
  spinMotor(motorFrontLeft, DC_SPEED, 2000);

  Serial.println("Step 8: Front left DC motor backward (2 sec)");
  spinMotor(motorFrontLeft, -DC_SPEED, 2000);

  Serial.println("Step 9: Front right DC motor forward (2 sec)");
  spinMotor(motorFrontRight, DC_SPEED, 2000);

  Serial.println("Step 10: Front right DC motor backward (2 sec)");
  spinMotor(motorFrontRight, -DC_SPEED, 2000);

  // 11. All four DC motors together
  Serial.println("Step 11: All DC motors forward (2 sec)");
  spinAllMotors(DC_SPEED, 2000);

  Serial.println("Step 12: All DC motors backward (2 sec)");
  spinAllMotors(-DC_SPEED, 2000);

  Serial.println("=== Motor test complete ===");
}

void loop() {
  runSteppers();
}