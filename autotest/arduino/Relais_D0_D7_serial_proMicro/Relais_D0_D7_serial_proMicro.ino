/* Pro Micro + Relaycard 8x Test Code
   by: Hans-Klaus Weiler
   date: November 26, 2019
   license: Public Domain - please use this code however you'd like.
   It's provided as a learning tool.

   This code is provided to show how to control the SparkFun
   ProMicro's D0..D7  within a sketch.
*/

// Each Arduino should identify when asked
// and show it's configuration (R8 = 8 relay)
String Ardu_ID =  "Arduino_0001";
String Ardu_config = "Ardu_config R8";

//define Relay for Arduino D0..D7
int Relay_0 = 0;
int Relay_1 = 1;
int Relay_2 = 2;
int Relay_3 = 3;
int Relay_4 = 4;
int Relay_5 = 5;
int Relay_6 = 6;
int Relay_7 = 7;

int RXLED = 17;  // The RX LED has a defined Arduino pin
int TXLED = 30;  // The TX LED has a defined Arduino pin


// CommandString for Relay will be Rx00..RxFF or RxMM00..RxMMFF where MM is mask
// the last two characters will be used as HEX for each bit to control a relais.
// The mask is used to leave relais in previous state if needed.
const int bufLength = 32;

bool CommandComplete = false;
char commandRead[bufLength] = "";
int  command_count=0;

void setup()
{
  //setup pins used for relay card D0..D7
  pinMode(Relay_0, OUTPUT);  // Set Relay_0 as an output
  pinMode(Relay_1, OUTPUT);  // Set Relay_1 as an output
  pinMode(Relay_2, OUTPUT);  // Set Relay_2 as an output
  pinMode(Relay_3, OUTPUT);  // Set Relay_3 as an output
  pinMode(Relay_4, OUTPUT);  // Set Relay_4 as an output
  pinMode(Relay_5, OUTPUT);  // Set Relay_5 as an output
  pinMode(Relay_6, OUTPUT);  // Set Relay_6 as an output
  pinMode(Relay_7, OUTPUT);  // Set Relay_7 as an output
  
  pinMode(RXLED, OUTPUT);  // Set RX LED as an output
  pinMode(TXLED, OUTPUT);  // Set TX LED as an output
  // pinMode(LED_BUILTIN, OUTPUT); //not available on proMicro


  //baud rate doesn't matter as we use USB
  Serial.begin(9600); //This pipes to the serial monitor
  //Serial.begin(921600); //This pipes to the serial monitor

  digitalWrite(RXLED, HIGH);    // set the RX LED OFF
  digitalWrite(TXLED, HIGH);    // set the TX LED OFF
 
  //init relais: OFF
  digitalWrite(Relay_0, HIGH);
  digitalWrite(Relay_1, HIGH);
  digitalWrite(Relay_2, HIGH);
  digitalWrite(Relay_3, HIGH);
  digitalWrite(Relay_4, HIGH);
  digitalWrite(Relay_5, HIGH);
  digitalWrite(Relay_6, HIGH);
  digitalWrite(Relay_7, HIGH);

  // wait for Serial to be active
  while (!Serial);
}

/*
 * Reads command from Serial, returns value.
 * timeout = milliseconds
 */
/*
 * 
 * 
char * read_command(unsigned long timeout) {
  bool CommandComplete = false;
  static char commandRead[bufLength] = "";
  unsigned long startmillis = millis();

  for (int i=0; i!= bufLength; i++) {
    Serial.print (".");
    commandRead[i]='\0';
    }
  while (!CommandComplete && (millis()-startmillis < timeout)) {
    while (Serial.available()) {
      digitalWrite(RXLED, LOW);    // set the RX LED ON
      commandRead[command_count] = Serial.read();
      if (commandRead[command_count] == '\n') {
        //other side answered, now send configuration
        CommandComplete = true;
      }
      else {
        command_count++;
      }
      digitalWrite(RXLED, HIGH);    // set the RX LED OFF
      }
      if (command_count == bufLength) {
        command_count = 0;
        digitalWrite(TXLED, LOW);    // set the TX LED ON
        Serial.println ("SerialRX Buffer overflow - buffer erased");
        digitalWrite(TXLED, HIGH);    // set the TX LED OFF      }
      }
    }
  //Serial.print ("Command read to return: ");
  //Serial.print (int(commandRead[15]));
  //Serial.println (commandRead);
  //Serial.println("Where comes the blob from");
  
  // Reset buffer and wait for next command
  command_count = 0;

  return commandRead;
}
*/


/*
 * setRelay(int RMaskComm)
 * parameter: int RMaskComm - first 2 bytes bitmask for setting relais
 *                          - second 2 bytes relais bitmask set/unset
 */
void setRelay(int RMaskComm) {
  byte RMask = (RMaskComm & 0xFF00) >> 8;
  byte RComm = (RMaskComm & 0x00FF);
  byte Rpins[] = {Relay_0, Relay_1, Relay_2, Relay_3, Relay_4, Relay_5, Relay_6, Relay_7};
  byte numRpins = sizeof(Rpins);
  digitalWrite(TXLED, LOW);    // set the TX LED ON
  Serial.print ("Set Relay RMask 0x");
  Serial.print (RMask, HEX);
  Serial.print (" RComm 0x");
  Serial.println (RComm, HEX);
  //Serial.println;
  digitalWrite(TXLED, HIGH);    // set the TX LED OFF
  for (byte i=0; i<numRpins; i++) {
    if (bitRead(RMask, i)) {
      digitalWrite(i, bitRead(RComm, i));   // set relais according to bit in parameter and mask
    }
  }
}


/*
 * loop in sketch:
 * - read command string from serial (usb):
 * - Rx (for Relay)
 * - MM hex for 8 relais bitmask
 * - RR hex for 8 relais set/unset
 * - '\n' to end string
 * 
 * when reading/writing Rx/TX LED are set
 */ 
void loop()
{
  String commandR2;
  //commandR2 = read_command(5000);
  while (Serial.available()) {
    //Serial.print ("Serial available: ");
    //Serial.print (Serial.available(), BIN);
    digitalWrite(RXLED, LOW);    // set the RX LED ON
    commandRead[command_count] = Serial.read();
  
    if (commandRead[command_count] == '\n') {
  //  if (commandR2.substring(0) == '\n') {
      CommandComplete = true;
      }
    else {
      command_count++;
      }
    }
  digitalWrite(RXLED, HIGH);    // set the RX LED OFF
  if (command_count == bufLength) {
    command_count = 0;
    digitalWrite(TXLED, LOW);    // set the TX LED ON
    Serial.println ("SerialRX Buffer overflow - buffer erased");
    digitalWrite(TXLED, HIGH);    // set the TX LED OFF
    }
 
// if command complete try to decode and set relais
  if (CommandComplete) {
    commandR2 = String(commandRead);
    CommandComplete = false;
    // check if AT command received
	// Board can send it's name (via AT I6)
	// and it's configuration (via AT I8)
    if (commandR2.startsWith("AT")) {
      if(commandR2.substring(2) == "I6\n") {
        Serial.println (Ardu_ID);    
      }
      else if (commandR2.substring(2) == "I8\n") {
        Serial.println (Ardu_config);            
      }
      else {
        Serial.print ("Unknown comand ");                    
        Serial.println (commandR2);                    
      }
    }
    //check if command for relais received
    //elseif (commandRead[0] == 'R' && commandRead[1] == 'x') {
    else if (commandR2.startsWith("Rx")) {
      if (command_count != 4 && command_count != 6) { 
        digitalWrite(TXLED, LOW);    // set the TX LED ON
        Serial.print("CommandError - Length command:");
        Serial.print(command_count, DEC);
        Serial.print(" command: ");
        Serial.println(commandRead);
        digitalWrite(TXLED, HIGH);    // set the TX LED OFF
      }
      else {
        //Serial.print("Command complete: ");     
        //Serial.print("Relay to set: ");
     
        if (command_count == 4) {
          setRelay( 0xFF00 | strtol(&commandRead[2], NULL, 16));
        } 
        else if (command_count == 6) {            
          setRelay(strtol(&commandRead[2], NULL, 16));
          }
        else {
          digitalWrite(TXLED, LOW);    // set the TX LED ON
          Serial.print ("Command error: can't decode ");
          Serial.println (commandRead);
          digitalWrite(TXLED, HIGH);    // set the TX LED OFF
        }
      }
    }
    else {
        Serial.print ("Unknown comand ");                    
        Serial.println (commandR2);                          
    }
  CommandComplete = false;
  command_count = 0;
  for (int i=0; i!= bufLength; i++) {
    commandRead[i]='\0';
    }

  }
}
