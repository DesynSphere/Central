// LabArduino 0.2 - 2025-11-17
  #include "DHT.h"    // DHT Sensor Library

// Arduino Mega
  const int HeaterACRelay = A1;     // Relay pin connection
  const int LEDRelay = A2;     // Relay pin connection
  const int DHTPin = 2;      // Digital Humidity and Temperature "DHT" sensor digital pin connection


// Variable
  // Time
    unsigned long Time = 0;     // Initial time
    const unsigned long TimeInterval = 2000;    // Time in millisecond between read/write/print
   
  // Temperature
    float AmbientTemperatureSetting = 5;       // Initial temperature setting
    float t = AmbientTemperatureSetting;       // Initial temperature reading
    float h = 0;                        // Initial humidity reading


// Hardware
  // Temperature & Humidity sensor
    #define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
    // Pin 1 (on the left) of the sensor to +5V
    // Pin 2 of the sensor to DHTPin
    // Pin 3 (on the right) of the sensor to GROUND
    DHT dht(DHTPin, DHTTYPE);     // Assign DHT sensor


// Setup
void setup() {
  Serial.begin(115200);     // Start serial monitor
  delay(200);     // Small delay to allow serial monitor/host to connect
  Serial.println(F("Arduino Ready"));
  
  pinMode(HeaterACRelay, OUTPUT);
  digitalWrite(HeaterACRelay, LOW);
  pinMode(LEDRelay, OUTPUT);
  digitalWrite(LEDRelay, LOW);

  // Temperature & Humidity sensor
  dht.begin();
}


// Loop
void loop() {
  handleIncoming();
  
  // Time
  Time = millis();  // Read the time
  if(Time % TimeInterval == 0){
    readAmbient();
    writeThermostat();
    printData();
  }
}

// Serial data/command
void handleIncoming() {
  static String line;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processLine(line);
      line = "";
    } else if (c != '\r') {
      line += c;
    }
  }
}
void processLine(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("LED:")) {
    int val = cmd.substring(4).toInt();
    digitalWrite(LEDRelay, val ? HIGH : LOW);
    Serial.print(F("OK LED:"));
    Serial.println(val ? 1 : 0);
  } else if (cmd.startsWith("AMBIENTTEMPERATURESETTING:")) {
    int val = cmd.substring(26).toInt();
    AmbientTemperatureSetting = val;
    Serial.print(F("OK AMBIENTTEMPERATURESETTING:"));
    Serial.print(AmbientTemperatureSetting);
    Serial.println(F("C"));
  } else if (cmd.equalsIgnoreCase("READ")) {
    printData();
  } else if (cmd.equalsIgnoreCase("PING")) {
    Serial.println(F("PONG"));
  } else {
    Serial.print(F("ERR Unknown cmd: "));
    Serial.println(cmd);
  }
}

// Ambient Temperature & Humidity
void readAmbient(){
    t = dht.readTemperature();    // Read temperature as Celsius (default)
    h = dht.readHumidity();   // Read humidity
    if (isnan(h) || isnan(t)){       // Check if any reads failed and exit early (to try again)
      Serial.println("DHT sensor read error");
      return;
    }
}
   
// Ambient Temperature Thermostat
void writeThermostat(){
  //if (t < AmbientTemperatureSetting[AmbientTempIncrement]){
  if (t < AmbientTemperatureSetting){
    digitalWrite(HeaterACRelay, HIGH);     // Turn on RelayHeater
  } 
  //if (t > AmbientTemperatureSetting[AmbientTempIncrement] + 0.5){
    if (t > AmbientTemperatureSetting + 0.5){
    digitalWrite(HeaterACRelay, LOW);     // Turn off RelayHeater
  } 
}

// Data print
void printData(){
    //Serial.print("Time: ");
    //Serial.print(Time/1000);
    //Serial.print("s ");
    Serial.print("AmbientTemperatureSetting: ");
    Serial.print(AmbientTemperatureSetting);
    Serial.print("C  ");
    Serial.print("AmbientTemperature: ");
    Serial.print(t);
    Serial.print("C  ");
    Serial.print("AmbientHumidity: ");
    Serial.print(h);
    Serial.print("%  ");
    Serial.print("HeaterACRelay: ");
    Serial.print(digitalRead(HeaterACRelay));
    Serial.println();
}
