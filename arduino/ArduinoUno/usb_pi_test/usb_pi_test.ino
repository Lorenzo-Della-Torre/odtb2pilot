void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(13, OUTPUT);
  Serial.println("Hello Pi 3, This is Aruino UNO...");

}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("Hello Pi 3, This is Arduino UNO...");
  if(Serial.available()){
    flash(Serial.parseInt());
    Serial.flush();
  }
  delay(1000);
  
}

void flash(int n){
  Serial.print("Flash times:");
  Serial.println(n);
  for (int i=0;i<n;i++){
    digitalWrite(13,HIGH);
    delay(500);
    digitalWrite(13,LOW);
    delay(500);
    Serial.println(i+1);
  }
  Serial.println("Flash complete");
}

