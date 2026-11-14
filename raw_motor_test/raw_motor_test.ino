// Raw pin test: no SparkFun library, one motor at a time.
// Each motor runs forward, pauses, runs backward, pauses.

struct RawMotor {
  const char *name;
  int in1;
  int in2;
  int pwm;
  int stby;
};

// Driver on pins 7-13 (called "F" in your code)
// Driver on pins 22-28 (called "B" in your code)
RawMotor motors[] = {
  { "Driver 7-13,  channel A (AIN) -> motor_left_back",   9,  8,  7, 10 },
  { "Driver 7-13,  channel B (BIN) -> motor_right_back", 11, 12, 13, 10 },
  { "Driver 22-28, channel A (AIN) -> motor_right_front", 24, 23, 22, 25 },
  { "Driver 22-28, channel B (BIN) -> motor_left_front",  26, 27, 28, 25 }
};
const int NUM_MOTORS = sizeof(motors) / sizeof(motors[0]);

const unsigned long RUN_MS = 2000;
const unsigned long PAUSE_MS = 1500;

void stopMotor(const RawMotor &m) {
  digitalWrite(m.pwm, LOW);
  digitalWrite(m.in1, LOW);
  digitalWrite(m.in2, LOW);
}

void runMotor(const RawMotor &m, bool forward) {
  digitalWrite(m.stby, HIGH);                 // take driver out of standby
  digitalWrite(m.in1, forward ? HIGH : LOW);
  digitalWrite(m.in2, forward ? LOW : HIGH);
  digitalWrite(m.pwm, HIGH);                  // full on (works on any pin)
  delay(RUN_MS);
  stopMotor(m);
  delay(PAUSE_MS);
}

void testMotor(const RawMotor &m) {
  Serial.println();
  Serial.println(m.name);

  Serial.println("  forward...");
  runMotor(m, true);

  Serial.println("  backward...");
  runMotor(m, false);
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_MOTORS; i++) {
    pinMode(motors[i].in1, OUTPUT);
    pinMode(motors[i].in2, OUTPUT);
    pinMode(motors[i].pwm, OUTPUT);
    pinMode(motors[i].stby, OUTPUT);
    digitalWrite(motors[i].stby, LOW);
    stopMotor(motors[i]);
  }

  Serial.println("=== Raw motor test start ===");
  for (int i = 0; i < NUM_MOTORS; i++) {
    testMotor(motors[i]);
  }
  Serial.println();
  Serial.println("=== Raw motor test complete ===");

  // Put drivers back in standby
  for (int i = 0; i < NUM_MOTORS; i++) {
    digitalWrite(motors[i].stby, LOW);
  }
}

void loop() {
  // Nothing: test runs once on reset.
}
