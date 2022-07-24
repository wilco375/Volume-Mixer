#include <LiquidCrystal.h>
#include <Arduino.h>
#include <RotaryEncoder.h>
#include <ezButton.h>

#define NUM_ENCODERS 3

// LCD
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Encoder
// Setup a RotaryEncoder with 2 steps per latch for the 2 signal input pins:
RotaryEncoder* encoders[] = {
  new RotaryEncoder(A0, A1, RotaryEncoder::LatchMode::TWO03),
  new RotaryEncoder(A2, A3, RotaryEncoder::LatchMode::TWO03),
  new RotaryEncoder(A4, A5, RotaryEncoder::LatchMode::TWO03)
};

// Buttons
ezButton* buttons[] = {
  new ezButton(6),
  new ezButton(7),
  new ezButton(8)
};

// Variables
char buff[5];
bool muted[NUM_ENCODERS] = {false};
int savedPos[NUM_ENCODERS] = {0};
int lastPos[NUM_ENCODERS] = {0};
int hasItem[NUM_ENCODERS] = {false};

/////////////////////////////////////////////////////////
//                     -- Setup --                     //
/////////////////////////////////////////////////////////
void setup()
{
  for (int i = 0; i < NUM_ENCODERS; i++) {
    buttons[i]->setDebounceTime(50);
  }

  Serial.begin(115200);
  while (!Serial);
  
  lcd.begin(16, 2);
} 


/////////////////////////////////////////////////////////
//                   -- LOOP START --                  //
/////////////////////////////////////////////////////////
void loop()
{
  // ------------------ Reading incomming messages ------------------------
  if (Serial.available()) {
    char separator = ',';
    String data = Serial.readString()+separator;
    int splitIndices[NUM_ENCODERS * 2 + 1] = {0};
    splitIndices[0] = -1;
    int found = 0;
    for (int i = 0; i < data.length(); i++) {
      if (data.charAt(i) == separator) {
        splitIndices[found + 1] = i;
        found++;
      }
    }
    
    for (int i = 0; i < NUM_ENCODERS; i++) {
      if (i * 2 + 1 < found) { 
        hasItem[i] = true;  
        String name = data.substring(splitIndices[i * 2] + 1, splitIndices[i * 2 + 1]);
        String volume = data.substring(splitIndices[i * 2 + 1] + 1, splitIndices[i * 2 + 2]);
        lcd.setCursor(i * 6, 0);
        lcd.print(name);
        lcd.setCursor(i * 6, 1);
        sprintf(buff, "%3d%%", volume);
        lcd.print(buff);
        encoders[i]->setPosition(volume.toInt());
      } else {
        // Make white
        hasItem[i] = false;
        lcd.setCursor(i * 6, 0);
        lcd.print("    ");
        lcd.setCursor(i * 6, 1);
        lcd.print("    ");
      }
    }
  }

  // --------------------------- Read encoders ----------------------------
  for (int i = 0; i < NUM_ENCODERS; i++) {
    if (!hasItem[i]) continue;
    
    encoders[i]->tick();

    int newPos = encoders[i]->getPosition();
    if (lastPos[i] != newPos) {
      if (newPos > 100){
        encoders[i]->setPosition(100);
        newPos = 100;
      }
      else if(newPos < 0){
        encoders[i]->setPosition(0);
        newPos = 0;
      }
      else {
        if (!muted[i]) {
          lcd.setCursor(i * 6, 1);
          sprintf(buff, "%3d%%", newPos);
          lcd.print(buff);
        }
      }

      Serial.println(String(i) + "," + String(newPos));
      lastPos[i] = newPos;
    }
  }
  
  // ------------------------- Read mute buttons --------------------------
  for (int i = 0; i < NUM_ENCODERS; i++) {
    if (!hasItem[i]) continue;
    
    buttons[i]->loop();

    if (buttons[i]->isReleased()) {
      muted[i] = !muted[i];
      if (muted[i]) {
        savedPos[i] = lastPos[i];
        encoders[i]->setPosition(0);
        lcd.setCursor(i * 6, 1);
        lcd.print("MUTE");
      } else {
        encoders[i]->setPosition(savedPos[i]);
      }
    }
  }
}
