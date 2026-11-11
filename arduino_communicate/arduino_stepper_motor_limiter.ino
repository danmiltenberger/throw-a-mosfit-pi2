//#include <ezButton.h>
//
//#define stp 2
//#define dir 3
//#define MS1 4
//#define MS2 5
//#define EN  6
//
//
//ezButton limitSwitch(50);
//
//char user_input;
//int x;
//int y;
//int state;
//int limiter_state;
//int iter;
//int i_crit;
//
//int full_rot_360 = 198;
//int defend_135 = 74;
//int shooting_rot_90 = 49;
//
//
////void setup() {
////
////  pinMode(stp, OUTPUT);
////  pinMode(dir, OUTPUT);
////  pinMode(MS1, OUTPUT);
////  pinMode(MS2, OUTPUT);
////  pinMode(EN, OUTPUT);
////
////  resetEDPins(); //Set step, direction, microstep and enable pins to default states
////  Serial.begin(9600); //Open Serial connection for debugging
////  Serial.println("Begin motor control");
////  Serial.println();
////
////  limitSwitch.setDebounceTime(50);
////}
//
////void loop() {
////
////  while(Serial.available()){ 
////      user_input = Serial.read(); 
////      digitalWrite(EN, LOW);
////
////
////     
////      if(user_input =='1') {
////        FullRotation();
////        Serial.println("Full Rotation");
////      }
////
////
////      else if(user_input == '2'){
////        defend();
////      }
////
////      else if(user_input == '3'){
////        Bring_Her_In();
////      }
////
////
////      else if(user_input == '4'){
////        shoot();
////      }
////
////      resetEDPins();
////      Serial.println("ready for new command");
////  }
////
////}
//
//void resetEDPins(){
//  digitalWrite(stp, LOW);
//  digitalWrite(dir, LOW);
//  digitalWrite(MS1, LOW);
//  digitalWrite(MS2, LOW);
//  digitalWrite(EN, HIGH);
//}
//
//void FullRotation(){
//  Serial.println("Finding Full rotation.");
//  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
//  for(x= 0; x<full_rot_360; x++)  //Loop the forward stepping enough times for motion to be visible
//  {
//    digitalWrite(stp,HIGH); //Trigger one step forward
//    delay(1);
//    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
//    delay(1);
//  }
//
//}
//
//void defend(){
//  Serial.println("Arms Extending, ready to defend");
//  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
//  for(x= 0; x<defend_135; x++)  //Loop the forward stepping enough times for motion to be visible
//  {
//    digitalWrite(stp,HIGH); //Trigger one step forward
//    delay(1);
//    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
//    delay(1);
//  }
//
//}
//
//void shoot (){
//  Serial.println("SHOOTING");
//  digitalWrite(dir, LOW); 
//  for(x= 0; x<shooting_rot_90; x++)  {
//    digitalWrite(stp,HIGH); //Trigger one step forward
//    delay(1);
//    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
//    delay(1);
//  }
//
//  delay(1000); 
//
//  digitalWrite(dir, HIGH); 
//  limiter_state = detect_limiter();
//  i_crit = shooting_rot_90;
//  while (limiter_state == HIGH && iter <= i_crit){
//    digitalWrite(stp,HIGH); //Trigger one step forward
//    delay(1);
//    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
//    delay(1);
//    limiter_state = detect_limiter();
//  }
//
//}
//
//void Bring_Her_In(){
//  Serial.println("Reeling her back");
//  digitalWrite(dir, HIGH); 
//  limiter_state = detect_limiter();
//  i_crit = 200;
//
//  while (limiter_state == HIGH && iter <= i_crit){
//    digitalWrite(stp,HIGH); 
//    delay(1);
//    digitalWrite(stp,LOW); 
//    delay(1);
//    limiter_state = detect_limiter();
//  }
//}
//
//int detect_limiter(){
//  limitSwitch.loop(); 
//
//  if(limitSwitch.isPressed()){
//    Serial.println("The limit switch: UNTOUCHED -> TOUCHED");
//  }
//
//  if(limitSwitch.isReleased()){
//    Serial.println("The limit switch: TOUCHED -> UNTOUCHED");
//  }
//
//  int state = limitSwitch.getState();
//  if(state == HIGH){
//    Serial.println("The limit switch: UNTOUCHED");
//  }
//  else{
//    Serial.println("The limit switch: TOUCHED");
//  }
//  return state;
//}
