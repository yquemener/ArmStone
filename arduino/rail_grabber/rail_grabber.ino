#include <Servo.h>

Servo myservo;  // create servo object
int pos = 130;    // variable to store the servo position
int attached = 0;
const int SERVO_PIN = 9;


void setup() {
  Serial.begin(9600); // opens serial port, sets data rate to 9600 bps
}

void loop() {
  if (Serial.available() > 0) {           // check if data is available to read
    int conf1 = Serial.parseInt();
    int temppos = Serial.parseInt();
    int conf2 = Serial.parseInt();              
    if (conf1==111 && conf2==222 && temppos >= 0 && temppos <= 180) {         // constrain the value between 0 and 180
      pos = temppos;
      myservo.write(pos);
      myservo.attach(SERVO_PIN);
      if(attached==0){
        
        attached=1;
      }
    }
    while (Serial.available() > 0) Serial.read();
  }

}
