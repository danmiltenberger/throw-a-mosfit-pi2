void respondToPi() {
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();  // Remove trailing carriage return or whitespace.

    if (message == "hello arduino!") {
      Serial.println("hello pi!");
    } else {
      Serial.print("arduino recieved: ");
      Serial.println(message);
    }
  }
}

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(1000);
}

void loop() {
  respondToPi();
}
