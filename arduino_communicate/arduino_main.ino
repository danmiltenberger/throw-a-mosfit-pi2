// TIME STAMP: 10/30/2026 429 PPF

// TODO
// test stepper motor
// test  request event arduino to pi
// write arm code 



//  LIBARIES ___________________________________________

#include <SparkFun_TB6612.h>
#include <stdlib.h>
#include <string.h>
#include <Wire.h>




// SENSOR CONFIGURATION

#define pinIRd_1 52
#define pinIRa_1 A14
#define pinIRd_2 53
#define pinIRa_2 A15

double track_color_white = 0.00;
double track_color_gray = 0.50;
double track_color_black = 1.00;

int sensor_left;
int sensor_right;

volatile byte Sensor_Status = 0; 
// 00: all is well, both sensors see black
// WHITE: 11: left sensor see white, 12: right sensor see white, 13 both sensors see white
// GRAY: 21: left sensor see gray, 22: right sensor see gray, 23 both sensors see gray



//  PADDLE MOTOR CONFIGURATION ___________________________________________

#define stp_1 2
#define dir_1 3
#define MS1_1 4
#define MS2_1 5
#define EN_1  6

#define stp_2 42
#define dir_2 43
#define MS1_2 44
#define MS2_2 45
#define EN_2  46


char user_input;
int x;
int y;
int state;


//  MOTOR CONFIGURATION ___________________________________________

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

const int offset_LF = 1;
const int offset_RF = 1;

const int offset_LB = 1;
const int offset_RB = 1;

float frontLeft; 
float frontRight;
float backLeft;
float backRight;

Motor motorLF = Motor(AIN1_F, AIN2_F, PWMA_F, offset_LF, STBY_F);
Motor motorRF = Motor(BIN1_F, BIN2_F, PWMB_F, offset_RF, STBY_F);

Motor motorLB = Motor(AIN1_B, AIN2_B, PWMA_B, offset_LB, STBY_B);
Motor motorRB = Motor(BIN1_B, BIN2_B, PWMB_B, offset_RB, STBY_B);

//int angle = 30; // ERROR: Degrees bewteen 0-90 output worng amount 
//int power = 1;

const int MOTOR_SPEED = 150; // Speed is constant whenever the robot is turning (0-255)


//  PI SETTINGS ___________________________________________

#define I2C_ADDRESS 0x08
#define PI_Serial 115200
const int DEADBAND = 12; // Ignore small errors when the object is near the center
char buffer[32]; // Buffer for messages received from the Raspberry Pi
int bufferIndex = 0;

String message;
volatile bool commandReady = false;
String receivedCommand = "";

volatile byte leftPayload_sensor = 0;
volatile byte rightPayload_sensor = 0;


// TEST 
// String message = "WHE|--Y|100\n"; // <WHE|++X|###>
// String message = "HAT_CYAN\n";
// int angle = 30; // ERROR: Degrees bewteen 0-90 output worng amount 
// int power = 1;
// MOT_CWO_100




//  SETUP 

void setup() {
  // PI COMMUNICATION 


  Serial.begin(115200);

  Wire.begin(0x08);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);



  // PADDLE MOTOR SETUP


  pinMode(stp_1, OUTPUT);
  pinMode(dir_1, OUTPUT);
  pinMode(MS1_1, OUTPUT);
  pinMode(MS2_1, OUTPUT);
  pinMode(EN_1, OUTPUT);

  pinMode(stp_2, OUTPUT);
  pinMode(dir_2, OUTPUT);
  pinMode(MS1_2, OUTPUT);
  pinMode(MS2_2, OUTPUT);
  pinMode(EN_2 OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states
  

  // SENSOR SETUP


  pinMode(pinIRd_1,INPUT);
  pinMode(pinIRa_1,INPUT);

  pinMode(pinIRd_2,INPUT);
  pinMode(pinIRa_2,INPUT);



  // SETUP
  Serial.println("Ready for I2C commands");
}

//  MAIN LOOP      

void loop() {

  // Sensor reading: sends info to PI upon request: info sent is [100, 50] (ie: [left sees black, right sees gray])
  left_color = check_sensor_reading (int pinIRa_1);
  right_color = check_sensor_reading (int pinIRa_2);
  leftPayload_sensor = (byte)(left_color);
  rightPayload_sensor = (byte)(right_color);

  if (commandReady) {
    noInterrupts();
    String command = receivedCommand;
    receivedCommand = "";
    commandReady = false;
    interrupts();

    Serial.print("Received: ");
    Serial.println(command);

    read_py(command);
  }
  
}



// FUNCTIONS _______________________________________________________________________________

void read_py (String command) {
  
    String operation = command.substring(0,1);
    int duration = command.substring(1,4).toInt()
  
    '''
  String system = command.substring(0,3);
  String direction = command.substring(4,7);
  String power_str = command.substring(8,11);
  int speed = power_str.toInt();
  String additional_info = command.substring(12,15);
  '''

    if (command == "SENSOR_STATUS") {
        respondToPi();
    }

    if (operation == "W") {
        wheel_go(duration);
    }
    
    if (operation == "S") {
        wheel_go_back(duration);
    }

    if (operation == "Q") {
        rotate_left(duration);
    }

    if (operation == "E") {
        rotate_right(duration);
    }

    if (operation == "A") {
        wheel_go_left(duration);
    }

    if (operation == "D") {
        wheel_go_right(duration);
    }

    if (operation == "B") {
        arm_out_block(duration);
    }

    if (operation == "I") {
        arm_in(duration);
    }

    if (operation == "K") {
        kick_it(duration);
    }

    



  if (system == "HAT"){
    String color = command.substring(4); 
    if (color == "CYAN"){
      dance();
    }
  }

}


void respondToPi() {
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();  // Remove trailing carriage return or whitespace.

    if (message == "SENSOR_STATUS") {
        Serial.print("arduino recieved: ");
        Serial.println(message);
        Serial.print("left sensor: ");
        Serial.println(leftPayload_sensor);
        Serial.print("right sensor: ");
        Serial.println(rightPayload_sensor);
        } else {
        Serial.print("arduino recieved: ");
        Serial.println(message);
        }
  }

  '''

    void setup() {
    Serial.begin(9600);
    Serial.setTimeout(1000);
    }

    void loop() {
    respondToPi();
    }
  }
    '''
}


void receiveEvent(int howMany) {
  while (Wire.available()) {
    char c = Wire.read();

    if (c != '\n' && c != '\r') {
      receivedCommand += c;
    }
  }

  commandReady = true;
}

void requestEvent() {
  byte dataBuffer[2];
  dataBuffer[0] = leftPayload_sensor;
  dataBuffer[1] = rightPayload_sensor;
  
  // Send the 2-byte series to the Pi
  Wire.write(dataBuffer, 2); 
}



void spin() {
  motor1.drive(100);
  motor2.drive(-100);
}

void shake(){
  left(motor1, motor2, 100);
  delay(1000);
  right(motor1, motor2, 100);
  delay(1000);
}

void dance(){
  for (int i = 0; i < 4; i++ ){
    forward(motor1, motor2, 150);
    delay(1000);
    back(motor1, motor2, 150);
    delay(1000);
  }
  left(motor1, motor2, 100);
  delay(1000);

  for (int i = 0; i < 4; i++ ){
    forward(motor1, motor2, 150);
    delay(1000);
    back(motor1, motor2, 150);
    delay(1000);
  }
  right(motor1, motor2, 100);
  delay(1000);
  
  Serial.println("DANCE");
}

void degree_to_wheel_drive (int angle) {
   int power = 1
  // Front Wheel / Back Right
  if (angle <= 90) {
    frontLeft = 100;
  }
  else if (angle <= 180) {
    frontLeft = 100 - (2.0 * (angle - 90.0) / 90.0) * 100;
  }
  else if (angle <= 270) {
    frontLeft = -100;
  }
  else {
    frontLeft = -100 + (2.0 * (angle - 270.0) / 90.0) * 100;
  }

  // Front Right / Back Left
  if (angle <= 90) {
    frontRight = 100 - (2.0 * angle / 90.0) * 100;
  }
  else if (angle <= 180) {
    frontRight = -100;
  }
  else if (angle <= 270) {
    frontRight = -100 + (2.0 * (angle - 180.0) / 90.0) * 100;
  }
  else {
    frontRight = 100;
  }
  frontRight = .01 * frontRight;
  frontLeft = .01 * frontLeft;
  backLeft = frontRight;
  backRight = frontLeft;
  
  motorLF.drive(power*frontLeft,1000);
  motorRF.drive(power*frontRight,1000);
  motorLB.drive(power*backLeft,1000);
  motorRB.drive(power*backRight,1000);
  Serial.print("Front Left:");
  Serial.print(power*frontLeft);
  Serial.print(" ");
  Serial.print("Front Right:");
  Serial.println(power*frontRight);
  Serial.print("Back Left:");
  Serial.print(power*backLeft);
  Serial.print(" ");
  Serial.print("Back Right:");
  Serial.println(power*backRight);
}

int check_sensor_reading (int pinIRa) {

  int IRvalueA = analogRead(pinIRa); // Sensor Left

  int color = closest_color(IRvalueA);

  return color;
}

void wheel_right_adjust () {
  right(motor1, motor2, 150);
  delay(100);
  Serial.println("adjusting left");
}

void wheel_go (int duration) {
    int speed = 150;
    forward(motorLF, motorRF, speed);
    forward(motorLB, motorRB, speed);
    delay(duration);
    Serial.println("dead ahead");    // DOES THIS PRINT ON SCREEN
}

void wheel_go_back (int duration) {
    int speed = 150;
    back(motorLF, motorRF, speed);
    back(motorLB, motorRB, speed);
    delay(duration);
    Serial.println("put it in reverse");    // DOES THIS PRINT ON SCREEN
}

void wheel_go_left (int duration) {
    int speed = 150;
    left(motorLF, motorRF, speed);
    left(motorLB, motorRB, speed);
    delay(duration);
    Serial.println("left");    // DOES THIS PRINT ON SCREEN
}

void wheel_go_right (int duration) {
    int speed = 150;
    right(motorLF, motorRF, speed);
    right(motorLB, motorRB, speed);
    delay(duration);
    Serial.println("right");    // DOES THIS PRINT ON SCREEN
}

void rotate_right (int duration) {
    int speed = 150;
    forward(motorLF, motorLB, speed);
    back(motorRF, motorRB, speed);
    delay(duration);
    Serial.println("rotating right");    // DOES THIS PRINT ON SCREEN
}

void rotate_left (int duration) {
    int speed = 150;
    back(motorLF, motorLB, speed);
    forward(motorRF, motorRB, speed);
    delay(duration);
    Serial.println("rotating left");    // DOES THIS PRINT ON SCREEN
}

void arm_out_block (int duration) {
    // TODO 
    ''' arms out to a 180 degree angle and holds for durations. used to block the ball from going into the goal. '''

    
}

void arm_in (int duration) {
    // TODO 
    ''' Arms pull back to proabably -45? must follow arm_block_out '''
}

void kick_it (int duration) {
    // TODO 
    '''quick out to 45 degress then back. More force/speed? '''
}

int closest_color (int A_read){
  int color;
  if (A_read > 900) {
    // black
    color = 100; 
  } 

  else if (A_read < 100) {
    // white
    color = 0;
  }

  else {
    // gray
    color = 50;
  }

  return color;

}
