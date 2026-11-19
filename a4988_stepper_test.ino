/*
  A4988 stepper motor test - two motors

  Wiring (Arduino Mega):
    Motor 1: D52 -> STEP, D53 -> DIR, D51 -> ENABLE (active LOW)
    Motor 2: D48 -> STEP, D49 -> DIR, D50 -> ENABLE (active LOW)
    Each A4988: RESET and SLEEP tied together
    Each A4988: VMOT/GND -> motor supply (8-35V) + 100uF cap across it
    Each A4988: VDD/GND  -> Arduino 5V/GND
    Each A4988: 1A/1B/2A/2B -> motor coils
    MS1/MS2/MS3 left unconnected = full step

  NEVER connect/disconnect a motor while the supply is powered.
*/

struct Motor {
  uint8_t stepPin;
  uint8_t dirPin;
  uint8_t enablePin;
};

const Motor MOTOR_1 = {52, 53, 51};
const Motor MOTOR_2 = {48, 49, 50};

const int STEPS_PER_REV = 200;   // 1.8 deg motor, full step. Use 200 * microstep factor otherwise.

void setupMotor(const Motor &m) {
  pinMode(m.stepPin, OUTPUT);
  pinMode(m.dirPin, OUTPUT);
  pinMode(m.enablePin, OUTPUT);
  digitalWrite(m.enablePin, HIGH);   // driver disabled until test runs
}

void setup() {
  Serial.begin(9600);
  setupMotor(MOTOR_1);
  setupMotor(MOTOR_2);
}

void loop() {
  Serial.println("Testing motor 1");
  testStepper(MOTOR_1, STEPS_PER_REV, 60);   // 1 rev at 60 RPM, each direction
  delay(1000);

  Serial.println("Testing motor 2");
  testStepper(MOTOR_2, STEPS_PER_REV, 60);
  delay(3000);
}

// Rotates one full revolution clockwise, pauses, then counter-clockwise.
// m: which motor's pins to use
// stepsPerRev: steps for one revolution (200 for full step, 3200 for 1/16 microstep)
// rpm: target speed
void testStepper(const Motor &m, int stepsPerRev, int rpm) {
  // Time for half of one step pulse, in microseconds
  unsigned long halfPulseUs = 60000000UL / ((unsigned long)stepsPerRev * rpm * 2);

  digitalWrite(m.enablePin, LOW);    // enable driver

  for (int dir = 1; dir >= 0; dir--) {
    Serial.println(dir ? "  Clockwise" : "  Counter-clockwise");
    digitalWrite(m.dirPin, dir);
    delayMicroseconds(5);            // A4988 needs DIR setup time

    for (int i = 0; i < stepsPerRev; i++) {
      digitalWrite(m.stepPin, HIGH);
      delayMicroseconds(halfPulseUs);
      digitalWrite(m.stepPin, LOW);
      delayMicroseconds(halfPulseUs);
    }
    delay(500);
  }

  digitalWrite(m.enablePin, HIGH);   // disable driver (motor free-wheels)
}
