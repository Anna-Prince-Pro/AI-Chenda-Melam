const int vibrationPin = 2;

int previousState = LOW;

void setup() {
  Serial.begin(9600);
  pinMode(vibrationPin, INPUT);

  Serial.println("AI Chenda Melam - Ready");
}

void loop() {

  int currentState = digitalRead(vibrationPin);

  // Detect a new vibration
  if (currentState == HIGH && previousState == LOW) {

    Serial.print("TAP,");
    Serial.println(millis());

    // Debounce: ignore repeated signals from same tap
    delay(200);
  }

  previousState = currentState;
}
