const int vibrationPin = 2;
const int dhumLedPin = 9;
const int taLedPin = 10;
const int onboardLedPin = LED_BUILTIN;

int previousState = LOW;

void setup() {
  Serial.begin(115200);

  pinMode(vibrationPin, INPUT);
  pinMode(dhumLedPin, OUTPUT);
  pinMode(taLedPin, OUTPUT);
  pinMode(onboardLedPin, OUTPUT);

  Serial.println("AI Chenda Melam - Ready");
}

void loop() {
  int currentState = digitalRead(vibrationPin);

  if (currentState == HIGH && previousState == LOW) {
    Serial.print("TAP,");
    Serial.println(millis());

    delay(80);
  }

  previousState = currentState;

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "LED,DHUM") {
      pulseLed(dhumLedPin);
    } else if (command == "LED,TA") {
      pulseLed(taLedPin);
    }
  }
}

void pulseLed(int pin) {
  digitalWrite(pin, HIGH);
  digitalWrite(onboardLedPin, HIGH);
  delay(35);
  digitalWrite(pin, LOW);
  digitalWrite(onboardLedPin, LOW);
}
