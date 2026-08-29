#include <Servo.h>

Servo chendaServo;

const int SERVO_PIN = 9;

void setup() {
  Serial.begin(9600);

  chendaServo.attach(SERVO_PIN);

  // Starting/rest position
  chendaServo.write(90);

  Serial.println("Servo Test Ready");
}

void loop() {
  // Strike movement
  chendaServo.write(40);
  delay(500);

  // Return to resting position
  chendaServo.write(90);
  delay(500);
}