#include <Servo.h>

Servo chendaServo;

const int SERVO_PIN = 9;

const int REST_POSITION = 40;
const int STRIKE_POSITION = 100;

void setup() {
  chendaServo.attach(SERVO_PIN);

  // Start at resting position
  chendaServo.write(REST_POSITION);

  delay(1000);
}

void loop() {

  // FAST DOWNWARD STRIKE
  chendaServo.write(STRIKE_POSITION);

  delay(80);

  // FAST RETURN
  chendaServo.write(REST_POSITION);

  delay(250);
}