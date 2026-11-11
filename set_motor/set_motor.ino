#include <SparkFun_TB6612.h>

// ---------- Direction constants ----------
const int FORWARD  =  1;
const int BACKWARD = -1;

// ---------- Pins ----------
// Front Wheels 
#define PWMA_F 7
#define AIN2_F 8
#define AIN1_F 9
#define STBY_F 10
#define BIN1_F 11 //right
#define BIN2_F 12 //right
#define PWMB_F 13

// Back Wheels
#define PWMA_B 22
#define AIN2_B 23
#define AIN1_B 24
#define STBY_B 25
#define BIN1_B 26 //right
#define BIN2_B 27 //right
#define PWMB_B 28

const int offset_LF = -1;
const int offset_RF = -1;
const int offset_LB = 1;
const int offset_RB = 1;

Motor motor_left_front  = Motor(BIN1_B, BIN2_B, PWMB_B, offset_RB, STBY_B);
Motor motor_left_back   = Motor(AIN1_F, AIN2_F, PWMA_F, offset_LF, STBY_F);

Motor motor_right_front = Motor(AIN1_B, AIN2_B, PWMA_B, offset_LB, STBY_B);
Motor motor_right_back  = Motor(BIN1_F, BIN2_F, PWMB_F, offset_RF, STBY_F);

#define TEST_SPEED 100   // percent (pins 22 and 28 only work at 100%)

// ---------- Non-blocking motor timing ----------
struct MotorTimer {
  Motor *motor;
  bool active;
  unsigned long startTime;
  unsigned long duration;
};

MotorTimer motorTimers[] = {
  { &motor_left_front,  false, 0, 0 },
  { &motor_right_front, false, 0, 0 },
  { &motor_left_back,   false, 0, 0 },
  { &motor_right_back,  false, 0, 0 }
};
const int NUM_MOTORS = sizeof(motorTimers) / sizeof(motorTimers[0]);

// speedPercent: 0-100, direction: FORWARD/BACKWARD, duration in ms
void set_motor(Motor &motor, int speedPercent, int direction, unsigned long duration) {
  speedPercent = constrain(speedPercent, 0, 100);
  int pwm = map(speedPercent, 0, 100, 0, 255);
  int signedSpeed = (direction >= 0) ? pwm : -pwm;

  for (int i = 0; i < NUM_MOTORS; i++) {
    if (motorTimers[i].motor == &motor) {
      motor.drive(signedSpeed);
      motorTimers[i].startTime = millis();
      motorTimers[i].duration  = duration;
      motorTimers[i].active    = true;
      return;
    }
  }
  Serial.println("set_motor: motor not registered in motorTimers");
}

// Call every loop(): brakes any motor whose duration has elapsed
void update_motors() {
  unsigned long now = millis();
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (motorTimers[i].active && (now - motorTimers[i].startTime >= motorTimers[i].duration)) {
      motorTimers[i].motor->brake();
      motorTimers[i].active = false;
    }
  }
}

// ---------- Mecanum movement ----------

void log_wheel(const char *name, int direction) {
  Serial.print("  ");
  Serial.print(name);
  Serial.print(": ");
  Serial.println(direction == FORWARD ? "FORWARD" : "BACKWARD");
}

void bot_move(const char *label, int dirLF, int dirRF, int dirLB, int dirRB,
              unsigned long duration) {
  Serial.print("[");
  Serial.print(millis());
  Serial.print(" ms] ");
  Serial.print(label);
  Serial.print(" | speed=");
  Serial.print(TEST_SPEED);
  Serial.print("% | duration=");
  Serial.print(duration);
  Serial.println(" ms");

  log_wheel("LF", dirLF);
  log_wheel("RF", dirRF);
  log_wheel("LB", dirLB);
  log_wheel("RB", dirRB);

  set_motor(motor_left_front,  TEST_SPEED, dirLF, duration);
  set_motor(motor_right_front, TEST_SPEED, dirRF, duration);
  set_motor(motor_left_back,   TEST_SPEED, dirLB, duration);
  set_motor(motor_right_back,  TEST_SPEED, dirRB, duration);
}

void bot_forward(unsigned long duration) {
  bot_move("BOT FORWARD", FORWARD, FORWARD, FORWARD, FORWARD, duration);
}

void bot_backward(unsigned long duration) {
  bot_move("BOT BACKWARD", BACKWARD, BACKWARD, BACKWARD, BACKWARD, duration);
}

// Strafe left: LF and RB backward, RF and LB forward
void bot_left(unsigned long duration) {
  bot_move("BOT STRAFE LEFT", BACKWARD, FORWARD, FORWARD, BACKWARD, duration);
}

// Strafe right: LF and RB forward, RF and LB backward
void bot_right(unsigned long duration) {
  bot_move("BOT STRAFE RIGHT", FORWARD, BACKWARD, BACKWARD, FORWARD, duration);
}

// Rotate left (counter-clockwise): left wheels backward, right wheels forward
void bot_rotate_left(unsigned long duration) {
  bot_move("BOT ROTATE LEFT", BACKWARD, FORWARD, BACKWARD, FORWARD, duration);
}

// Rotate right (clockwise): left wheels forward, right wheels backward
void bot_rotate_right(unsigned long duration) {
  bot_move("BOT ROTATE RIGHT", FORWARD, BACKWARD, FORWARD, BACKWARD, duration);
}

// ---------- System check (call manually if needed) ----------

const unsigned long CHECK_MS = 6000;  // run time per direction
const unsigned long GAP_MS   = 6000;  // pause between steps

void wait_ms(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    update_motors();
  }
}

void check_one(Motor &motor, const char *name) {
  Serial.print(name);
  Serial.println(" Forward");
  set_motor(motor, TEST_SPEED, FORWARD, CHECK_MS);
  wait_ms(CHECK_MS + GAP_MS);

  Serial.print(name);
  Serial.println(" Backward");
  set_motor(motor, TEST_SPEED, BACKWARD, CHECK_MS);
  wait_ms(CHECK_MS + GAP_MS);
}

void system_check() {
  Serial.println("=== System check start ===");
  check_one(motor_left_front,  "Front Left");
  check_one(motor_right_front, "Front Right");
  check_one(motor_left_back,   "Back Left");
  check_one(motor_right_back,  "Back Right");
  Serial.println("=== System check complete ===");
}

// ---------- Serial command handling ----------

const float MAX_DURATION_S = 10.0;  // safety cap per command
String cmdBuffer = "";

// Parses and runs a command like "W2.0"
void run_command(String cmd) {
  cmd.trim();
  if (cmd.length() < 2) {
    Serial.println("Invalid command. Format: <letter><seconds>, e.g. W2.0");
    return;
  }

  char letter = toupper(cmd.charAt(0));
  float seconds = cmd.substring(1).toFloat();

  if (seconds <= 0) {
    Serial.println("Invalid duration. Example: W2.0");
    return;
  }
  if (seconds > MAX_DURATION_S) {
    Serial.print("Duration capped at ");
    Serial.print(MAX_DURATION_S);
    Serial.println(" s");
    seconds = MAX_DURATION_S;
  }

  unsigned long ms = (unsigned long)(seconds * 1000.0);

  Serial.print("Command: ");
  Serial.print(letter);
  Serial.print(" for ");
  Serial.print(seconds, 1);
  Serial.println(" s");

  switch (letter) {
    case 'W': bot_forward(ms);      break;
    case 'S': bot_backward(ms);     break;
    case 'A': bot_left(ms);         break;
    case 'D': bot_right(ms);        break;
    case 'Q': bot_rotate_left(ms);  break;
    case 'E': bot_rotate_right(ms); break;
    default:
      Serial.print("Unknown command '");
      Serial.print(letter);
      Serial.println("'. Use W, A, S, D, Q, or E.");
      break;
  }
}

// Reads serial characters without blocking; runs a command on newline
void read_serial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdBuffer.length() > 0) {
        run_command(cmdBuffer);
        cmdBuffer = "";
      }
    } else {
      cmdBuffer += c;
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Ready. W/S/A/D = forward/backward/left/right, Q/E = rotate left/right");
  Serial.println("Example: W2.0 = forward for 2 seconds");
}

void loop() {
  read_serial();
  update_motors();  // must be called every loop
}
