#include <AccelStepper.h>

#define motorInterfaceType 1

// ---------- Steppers ----------
#define STEPPER_R_DIR 22    // gray
#define STEPPER_R_STEP 24   // purple
#define STEPPER_R_EN 26     // yellow

#define STEPPER_L_DIR 23    // blue
#define STEPPER_L_STEP 25   // purple
#define STEPPER_L_EN 27     // yellow

// ------ Limit Switches ------
#define STEPPER_L_LIM_SWITCH 28
#define STEPPER_R_LIM_SWITCH 29

// Wired to GND with INPUT_PULLUP: pressed = LOW.
// Change to HIGH if your switches are wired normally-closed or to 5V.
#define LIM_SWITCH_TRIGGERED LOW

// ---------- Stepper settings ----------
#define STEPPER_EN_ACTIVE LOW        // LOW = enabled

// Steps per full revolution: 200 x microstepping.
// Set the multiplier to match your driver's microstep setting (1 = full step).
const float STEPS_PER_REV = 200.0 * 1;

// Speed/accel for all normal moves (must be >= HOMING_SPEED)
#define MOVE_MAX_SPEED      400.0    // steps/sec
#define MOVE_ACCELERATION   1000.0   // steps/sec^2

// ---------- Homing settings ----------
#define HOMING_SPEED        150.0    // steps/sec
#define HOMING_DIRECTION_L  1        // +1 = clockwise, -1 = counterclockwise
#define HOMING_DIRECTION_R  1        // flip to -1 if the right motor moves away from its switch
#define HOMING_TIMEOUT_MS   30000UL  // give up if the switch is never hit
#define HOMING_PAUSE_MS     500      // pause between homing steps

// ---------- Position settings (degrees away from home) ----------
#define OUT_DEGREES         225.0    // OUT command
#define IN_DEGREES          5.0      // IN command (stops just short of the switch)
#define KICK_DEGREES        135.0    // KICK command peak
#define KICK_RETURN_DEGREES IN_DEGREES  // KICK returns to the IN position

// ---------- Stepper objects ----------
AccelStepper stepperL(motorInterfaceType, STEPPER_L_STEP, STEPPER_L_DIR);
AccelStepper stepperR(motorInterfaceType, STEPPER_R_STEP, STEPPER_R_DIR);

bool isHomed = false;   // true once both steppers have homed successfully

long degreesToSteps(float degrees) {
  return round(degrees * STEPS_PER_REV / 360.0);
}

// Test function: prints when each limit switch is pressed/released
void testLimitSwitches() {
  static bool lastL = false;
  static bool lastR = false;
  static unsigned long lastChangeL = 0;
  static unsigned long lastChangeR = 0;
  const unsigned long debounceMs = 20;

  bool currentL = (digitalRead(STEPPER_L_LIM_SWITCH) == LIM_SWITCH_TRIGGERED);
  bool currentR = (digitalRead(STEPPER_R_LIM_SWITCH) == LIM_SWITCH_TRIGGERED);
  unsigned long now = millis();

  if (currentL != lastL && (now - lastChangeL) > debounceMs) {
    lastL = currentL;
    lastChangeL = now;
    Serial.println(currentL ? "LEFT limit switch TRIGGERED" : "LEFT limit switch released");
  }

  if (currentR != lastR && (now - lastChangeR) > debounceMs) {
    lastR = currentR;
    lastChangeR = now;
    Serial.println(currentR ? "RIGHT limit switch TRIGGERED" : "RIGHT limit switch released");
  }
}

// Rotates a stepper at constant slow speed until its limit switch triggers,
// then sets that position as home (0). Returns true on success.
bool homeStepper(AccelStepper &stepper, int enPin, int limPin, int direction, const char *name) {
  Serial.print("Homing ");
  Serial.print(name);
  Serial.println(" stepper...");

  digitalWrite(enPin, STEPPER_EN_ACTIVE);   // enable driver
  delay(100);                               // let the driver settle

  // If the switch is already pressed, don't drive into it
  if (digitalRead(limPin) == LIM_SWITCH_TRIGGERED) {
    Serial.print(name);
    Serial.println(" limit switch already triggered. Setting home here.");
    stepper.setCurrentPosition(0);
    return true;
  }

  stepper.setSpeed(direction * HOMING_SPEED);

  unsigned long start = millis();

  while (digitalRead(limPin) != LIM_SWITCH_TRIGGERED) {
    if (millis() - start > HOMING_TIMEOUT_MS) {
      Serial.print("Homing FAILED for ");
      Serial.print(name);
      Serial.println(": timed out before reaching limit switch");
      digitalWrite(enPin, !STEPPER_EN_ACTIVE);  // disable driver
      return false;
    }
    stepper.runSpeed();   // steps at constant speed when due
  }

  stepper.setCurrentPosition(0);   // this is now home
  Serial.print(name);
  Serial.println(" stepper homed. Position set to 0.");
  return true;
}

// Homes left, then right, one at a time. Returns true only if both succeed.
bool homeAllSteppers() {
  bool leftOk = homeStepper(stepperL, STEPPER_L_EN, STEPPER_L_LIM_SWITCH, HOMING_DIRECTION_L, "LEFT");
  if (!leftOk) {
    Serial.println("Aborting: left homing failed, skipping right.");
    return false;
  }

  delay(HOMING_PAUSE_MS);

  bool rightOk = homeStepper(stepperR, STEPPER_R_EN, STEPPER_R_LIM_SWITCH, HOMING_DIRECTION_R, "RIGHT");
  if (!rightOk) {
    // Don't leave the left motor energized if the sequence failed
    digitalWrite(STEPPER_L_EN, !STEPPER_EN_ACTIVE);
    return false;
  }

  Serial.println("Both steppers homed.");
  return true;
}

// Moves both arms to an absolute angle measured AWAY from home
// (opposite of each motor's homing direction). Blocks until both arrive.
void moveBothToDegreesAway(float degrees) {
  long steps = degreesToSteps(degrees);

  stepperL.moveTo(-HOMING_DIRECTION_L * steps);
  stepperR.moveTo(-HOMING_DIRECTION_R * steps);

  while (stepperL.distanceToGo() != 0 || stepperR.distanceToGo() != 0) {
    stepperL.run();
    stepperR.run();
  }
}

// ---------- Command handlers ----------

void doHome() {
  isHomed = false;
  if (homeAllSteppers()) {
    isHomed = true;
    delay(HOMING_PAUSE_MS);
    Serial.println("Moving to IN position (5 degrees from home)...");
    moveBothToDegreesAway(IN_DEGREES);
    Serial.println("HOME complete.");
  }
}

void doOut() {
  Serial.println("OUT: moving to 225 degrees from home...");
  moveBothToDegreesAway(OUT_DEGREES);
  Serial.println("OUT complete.");
}

void doKick() {
  Serial.println("KICK: moving to 135 degrees from home...");
  moveBothToDegreesAway(KICK_DEGREES);
  Serial.println("KICK: returning to 5 degrees from home...");
  moveBothToDegreesAway(KICK_RETURN_DEGREES);
  Serial.println("KICK complete.");
}

void doIn() {
  Serial.println("IN: moving to 5 degrees from home...");
  moveBothToDegreesAway(IN_DEGREES);
  Serial.println("IN complete.");
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  if (cmd.length() == 0) return;

  if (cmd == "HOME") {
    doHome();
    return;
  }

  if (cmd == "OUT" || cmd == "KICK" || cmd == "IN") {
    if (!isHomed) {
      Serial.println("Not homed. Send HOME first.");
      return;
    }
    if (cmd == "OUT")       doOut();
    else if (cmd == "KICK") doKick();
    else                    doIn();
    return;
  }

  Serial.print("Unknown command: ");
  Serial.println(cmd);
  Serial.println("Valid commands: OUT, KICK, IN, HOME");
}

// Collects characters until a newline, then runs the command
void readSerialCommands() {
  static String buffer = "";

  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        handleCommand(buffer);
        buffer = "";
      }
    } else {
      buffer += c;
    }
  }
}

void setup() {
  // Disable drivers first while everything is configured
  pinMode(STEPPER_L_EN, OUTPUT);
  pinMode(STEPPER_R_EN, OUTPUT);
  digitalWrite(STEPPER_L_EN, !STEPPER_EN_ACTIVE);
  digitalWrite(STEPPER_R_EN, !STEPPER_EN_ACTIVE);

  Serial.begin(9600);
  delay(1000);

  pinMode(STEPPER_L_LIM_SWITCH, INPUT_PULLUP);
  pinMode(STEPPER_R_LIM_SWITCH, INPUT_PULLUP);

  // Without setMaxSpeed(), AccelStepper caps speed at 1 step/sec
  stepperL.setMaxSpeed(MOVE_MAX_SPEED);
  stepperL.setAcceleration(MOVE_ACCELERATION);
  stepperR.setMaxSpeed(MOVE_MAX_SPEED);
  stepperR.setAcceleration(MOVE_ACCELERATION);

  Serial.println("Ready.");

  doHome();   // same sequence as the HOME command

  Serial.println("Commands: OUT, KICK, IN, HOME");
}

void loop() {
  readSerialCommands();
  testLimitSwitches();   // still prints switch events
}
