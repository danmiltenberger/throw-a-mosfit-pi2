// TIME STAMP: 10/30/2026 429 PPF

// TODO
// test stepper motor
// test  request event arduino to pi

// ISSUES
/*

degree to wheel drive 

*/




//  LIBARIES ___________________________________________

#include <SparkFun_TB6612.h>
#include <stdlib.h>
#include <string.h>
// #include <Wire.h>
#include <ezButton.h>

// SENSOR CONFIGURATION ___________________________________________

#define pinIRd_1 52
#define pinIRa_1 A14
#define pinIRd_2 53
#define pinIRa_2 A15


double track_color_white = 0.00;
double track_color_gray = 0.50;
double track_color_black = 1.00;

int sensor_left;
int sensor_right;

int left_color;
int right_color;

volatile byte Sensor_Status = 0; 
// 00: all is well, both sensors see black
// WHITE: 11: left sensor see white, 12: right sensor see white, 13 both sensors see white
// GRAY: 21: left sensor see gray, 22: right sensor see gray, 23 both sensors see gray



//  PADDLE MOTOR CONFIGURATION ___________________________________________
// left
#define stp_1 2
#define dir_1 3
#define MS1_1 4
#define MS2_1 5
#define EN_1  6

// right
#define stp_2 42
#define dir_2 43
#define MS1_2 44
#define MS2_2 45
#define EN_2  46

ezButton limitSwitch(50);

char user_input;
int x;
int y;
int limiter_state;
int iter;
int i_crit;

int full_rot_360 = 198;
int defend_135 = 74;
int shooting_rot_90 = 49;


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

const int motor_speed = 255; // we can only run full speed, unless we switch (22, 28) solution? (44–46 are free if we move stepper 2’s MS1/MS2/EN to plain digital pins) ie 


//  PI SETTINGS ___________________________________________

// #define I2C_ADDRESS 0x08
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





//  SETUP 

void setup() {
  // PI COMMUNICATION 


  Serial.begin(PI_Serial);

  // Wire.begin(I2C_ADDRESS);
  // Wire.onReceive(receiveEvent);
  // Wire.onRequest(requestEvent);



  // PADDLE STEPPER MOTOR SETUP


  pinMode(stp_1, OUTPUT);
  pinMode(dir_1, OUTPUT);
  pinMode(MS1_1, OUTPUT);
  pinMode(MS2_1, OUTPUT);
  pinMode(EN_1, OUTPUT);

  pinMode(stp_2, OUTPUT);
  pinMode(dir_2, OUTPUT);
  pinMode(MS1_2, OUTPUT);
  pinMode(MS2_2, OUTPUT);
  pinMode(EN_2, OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states

  limitSwitch.setDebounceTime(50);
  

  // SENSOR SETUP


  pinMode(pinIRd_1,INPUT);
  pinMode(pinIRa_1,INPUT);

  pinMode(pinIRd_2,INPUT);
  pinMode(pinIRa_2,INPUT);



  // SETUP

  Serial.println("READY");
  
}

//  MAIN LOOP      

void loop() {

  // Sensor reading: sends info to PI upon request: info sent is [100, 50] (ie: [left sees black, right sees gray])
  left_color = check_sensor_reading (pinIRa_1);
  right_color = check_sensor_reading (pinIRa_2);
  leftPayload_sensor = (byte)(left_color);
  rightPayload_sensor = (byte)(right_color);

  readSerialCommand(); // Read command from Serial (Pi)

  
  if (commandReady) {

    
    String command = receivedCommand;
    receivedCommand = "";
    commandReady = false;
    

    Serial.print("ACK "); 
    Serial.print(command);
    Serial.print(" "); 
    Serial.print(leftPayload_sensor); 
    Serial.print(" "); 
    Serial.println(rightPayload_sensor);

    read_py(command);
  }
  
  
}



// FUNCTIONS _______________________________________________________________________________

void read_py (String command) {
    String operation = command.substring(0,1);
    int duration = command.substring(1).toInt();

    if (operation == "W") {
        wheel_go(duration);
    }
    
    else if (operation == "S") {
        wheel_go_back(duration);
    }

    else if (operation == "Q") {
        rotate_left(duration);
    }

    else if (operation == "E") {
        rotate_right(duration);
    }

    else if (operation == "A") {
        wheel_go_left(duration);
    }

    else if (operation == "D") {
        wheel_go_right(duration);
    }

    else if (operation == "B") {
        arm_out_block();
    }

    else if (operation == "I") {
        bring_her_in();
    }

    else if (operation == "K") {
      kick_it();
    }

    else if (operation == "P") {
      Serial.print("arduino recieved: ");
      Serial.println(operation);
      Serial.print("left sensor: ");
      Serial.println(leftPayload_sensor);
      Serial.print("right sensor: ");
      Serial.println(rightPayload_sensor);
    } 

    else {
      Serial.print("arduino recieved: ");
      Serial.println(command);
    }

    resetEDPins();

}

// FUNCTIONS _______________________________________________________________________________


// I2C OR USB SERIAL COMMUNICATION _______________________________________________________________________________
/*
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
*/

void readSerialCommand() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (receivedCommand.length() > 0) commandReady = true;
      return;
    }
    if (c != '\r') receivedCommand += c;
  }
}



// EXTRA FUNCTIONS _______________________________________________________________________________
void spin() {
  motorLF.drive(motor_speed);
  motorLB.drive(motor_speed);
  motorRF.drive(-motor_speed);
  motorRB.drive(-motor_speed);
}

void shake(){
  left(motorLF, motorRF, motor_speed);
  delay(1000);
  right(motorLF, motorRF, motor_speed);
  delay(1000);
}

void dance(){
  for (int i = 0; i < 4; i++ ){
    forward(motorLF, motorRF, motor_speed);
    delay(1000);
    back(motorLF, motorRF, motor_speed);
    delay(1000);
  }
  left(motorLF, motorRF, motor_speed);
  delay(1000);

  for (int i = 0; i < 4; i++ ){
    forward(motorLF, motorRF, motor_speed);
    delay(1000);
    back(motorLF, motorRF, motor_speed);
    delay(1000);
  }
  right(motorLF, motorRF, motor_speed);
  delay(1000);
  
  Serial.println("DANCE");
}


// WHEEL FUNCTIONS _______________________________________________________________________________
void degree_to_wheel_drive (int angle) { // riddled with errors
   int power = 1;
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

void stop_dear_god_please_stop () {
    brake(motorLF, motorRF); 
    brake(motorLB, motorRB);
}

void wheel_go (int duration) {
    Serial.println("dead ahead");    // DOES THIS PRINT ON SCREEN
    forward(motorLF, motorRF, motor_speed);
    forward(motorLB, motorRB, motor_speed);
    drive_for(duration);


}

void wheel_go_back (int duration) {
    back(motorLF, motorRF, motor_speed);
    back(motorLB, motorRB, motor_speed);
    drive_for(duration);
    Serial.println("put it in reverse");    // DOES THIS PRINT ON SCREEN

}

void wheel_go_left (int duration) {
    motorLF.drive(-motor_speed);
    motorRF.drive( motor_speed);
    motorLB.drive( motor_speed);
    motorRB.drive(-motor_speed);

  /* CHANGE IF PWM pins are moved to 44-46
    left(motorLF, motorRF, motor_speed);
    right(motorLB, motorRB, motor_speed);
  */
    drive_for(duration);
    Serial.println("left");    // DOES THIS PRINT ON SCREEN

}

void wheel_go_right (int duration) {
    motorLF.drive( motor_speed);
    motorRF.drive(-motor_speed);
    motorLB.drive(-motor_speed);
    motorRB.drive( motor_speed);

    /* CHANGE IF PWM pins are moved to 44-46
    right(motorLF, motorRF, motor_speed);
    left(motorLB, motorRB, motor_speed);
    */ 
    drive_for(duration);
    Serial.println("right");    // DOES THIS PRINT ON SCREEN

}

void rotate_right (int duration) { 
    forward(motorLF, motorLB, motor_speed);
    back(motorRF, motorRB, motor_speed);
    delay(duration);
    stop_dear_god_please_stop();
    Serial.println("rotating right");    // DOES THIS PRINT ON SCREEN


}

void rotate_left (int duration) { 
    back(motorLF, motorLB, motor_speed);
    forward(motorRF, motorRB, motor_speed);
    delay(duration);
    stop_dear_god_please_stop();
    Serial.println("rotating left");    // DOES THIS PRINT ON SCREEN
}



// ARM FUNCTIONS _______________________________________________________________________________
void resetEDPins(){
  digitalWrite(stp_1, LOW);
  digitalWrite(dir_1, LOW);
  digitalWrite(MS1_1, LOW);
  digitalWrite(MS2_1, LOW);
  digitalWrite(EN_1, HIGH);

  digitalWrite(stp_2, LOW);
  digitalWrite(dir_2, LOW);
  digitalWrite(MS1_2, LOW);
  digitalWrite(MS2_2, LOW);
  digitalWrite(EN_2, HIGH);
}

int detect_limiter(){
  limitSwitch.loop(); 

  /*
  if(limitSwitch.isPressed()){
    Serial.println("The limit switch: UNTOUCHED -> TOUCHED");
  }

  if(limitSwitch.isReleased()){
    Serial.println("The limit switch: TOUCHED -> UNTOUCHED");
  }

  if(state == HIGH){
    Serial.println("The limit switch: UNTOUCHED");
  }
  else{
    Serial.println("The limit switch: TOUCHED");
  }
  */
  return limitSwitch.getState();
}

void defend(){
  digitalWrite(EN_1, LOW);
  digitalWrite(EN_2, LOW);

  Serial.println("Arms Extending, ready to defend");
  digitalWrite(dir_1, LOW); 
  digitalWrite(dir_2, HIGH);

  for(x= 0; x<defend_135; x++)  {
    digitalWrite(stp_1,HIGH); //Trigger one step forward
    digitalWrite(stp_2,HIGH);
    delay(1);
    digitalWrite(stp_1,LOW); //Pull step pin low so it can be triggered again
    digitalWrite(stp_2,LOW);
    delay(1);
  }

}

void kick_it (){
  digitalWrite(EN_1, LOW);
  digitalWrite(EN_2, LOW);

  Serial.println("SHOOTING");
  digitalWrite(dir_1, LOW); 
  digitalWrite(dir_2, HIGH);

  for(x= 0; x<shooting_rot_90; x++)  {
    digitalWrite(stp_1,HIGH); //Trigger one step forward
    digitalWrite(stp_2,HIGH);
    delay(1);
    digitalWrite(stp_1,LOW); //Pull step pin low so it can be triggered again
    digitalWrite(stp_2,LOW);
    delay(1);
  }

  delay(1000); 

  digitalWrite(dir_1, HIGH); 
  digitalWrite(dir_2, LOW);
  limiter_state = detect_limiter();
  iter = 0;
  i_crit = shooting_rot_90;

  while (limiter_state == HIGH && iter <= i_crit){
    digitalWrite(stp_1,HIGH); //Trigger one step forward
    digitalWrite(stp_2,HIGH);
    delay(1);
    digitalWrite(stp_1,LOW); //Pull step pin low so it can be triggered again
    digitalWrite(stp_2,LOW);
    delay(1);
    limiter_state = detect_limiter();
    iter = iter + 1;
  }

}

void bring_her_in(){
  digitalWrite(EN_1, LOW);
  digitalWrite(EN_2, LOW);

  Serial.println("Reeling her back");
  digitalWrite(dir_1, HIGH);
  digitalWrite(dir_2, LOW);  // ADD THE OTHER MOTOR (RIGHT)
  limiter_state = detect_limiter();
  iter = 0;
  i_crit = 200;

  while (limiter_state == HIGH && iter <= i_crit){
    digitalWrite(stp_1,HIGH); 
    digitalWrite(stp_2,HIGH);
    delay(1);
    digitalWrite(stp_1,LOW); 
    digitalWrite(stp_2,LOW);
    delay(1);
    limiter_state = detect_limiter();
    iter = iter + 1;
  }
}


void arm_out_block () {
    // arms out to a 180 degree angle and holds for durations. used to block the ball from going into the goal. //

    defend(); 
    delay(2000);
    bring_her_in();

    
}


//  SENSOR READING _______________________________________________________________________________
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

int check_sensor_reading (int pinIRa) {

  int IRvalueA = analogRead(pinIRa); // Sensor Left

  int color = closest_color(IRvalueA);

  return color;
}

void drive_for(int duration) {
  bool startedOnWhite = (check_sensor_reading(pinIRa_1) == 0 || check_sensor_reading(pinIRa_2) == 0);

  unsigned long start = millis();
  while (millis() - start < duration) {
    int l = check_sensor_reading(pinIRa_1);
    int r = check_sensor_reading(pinIRa_2);
    leftPayload_sensor = l;
    rightPayload_sensor = r;

    bool onWhite = (l == 0 || r == 0);
    if (onWhite && !startedOnWhite) {
      Serial.println("WHITE - stopping");
      break;
    }
    if (!onWhite) startedOnWhite = false;   // left the line, re-arm the check
  }
  stop_dear_god_please_stop();
}