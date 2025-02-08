/*      
        SOUNDMIXER MK2
        CUSTOM PCB, ESP32, 480x320 TFT SCREEN

        MADE BY: Arjen van Dijk
                 Wilco van Beijnum
*/ 

//    --- LIBRARY ---
#include "Background.h"                                // Background image in bitmap format
#include <TFT_eSPI.h>                       // Hardware-specific library
#include <SPI.h>                            // SPI needed to comunicate with screen
TFT_eSPI tft = TFT_eSPI();                             // Invoke custom library
#include "AiEsp32RotaryEncoder.h"                      // Encoder Library with button and acceleration featueres
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;           
           
//    --- VARIABLES ---           
#define BT_NAME "SoundMixer"                           // Bluetooth name 
#define NUM_APP_ENCODERS 3           
#define NUM_ENCODERS NUM_APP_ENCODERS + 2           
#define VOL_BAR_WIDTH 100                              // Width of the vol_bar of the individual apps
#define VOL_BAR_HEIGHT 13                              // Height of the vol-bar of the individual apps
int APP_X_POS[] = {95, 240, 385};                      // X coordinates of individual apps

int prevVolumes[NUM_ENCODERS] = {-1, -1, -1, -1, -1};  // Array to store previous volume values for individual apps and main volume
String *apps;                                          // Pointer to array storing names of individual apps
int *volumes;                                          // Pointer to array storing volume levels of individual apps
int mainVolume = 0;                                    // Main volume level
int programIndex = 0;                                  // Starting point for cycling apps
int numApps = 0;                                       // How many apps are there
int prevTextWidth[NUM_APP_ENCODERS] = {0, 0, 0};       // keep track of previous text width for all three app spots

// Main volume encoder
#define ENCODER_1A 5
#define ENCODER_1B 19
#define ENCODER_1SW 21

// Selecter encoder
#define ENCODER_2A 13
#define ENCODER_2B 12
#define ENCODER_2SW 14

// App 1 endoder
#define ENCODER_5A 25
#define ENCODER_5B 26
#define ENCODER_5SW 27

// App 2 encoder
#define ENCODER_4A 32
#define ENCODER_4B 35
#define ENCODER_4SW 33

// App 3 encoder
#define ENCODER_3A 39
#define ENCODER_3B 36
#define ENCODER_3SW 34

#define ENCODER_STEPS 4

AiEsp32RotaryEncoder rotaryEncoders[] = {
  AiEsp32RotaryEncoder(ENCODER_5A, ENCODER_5B, ENCODER_5SW, -1, ENCODER_STEPS), // App 1 endoder
  AiEsp32RotaryEncoder(ENCODER_4A, ENCODER_4B, ENCODER_4SW, -1, ENCODER_STEPS), // App 2 encoder
  AiEsp32RotaryEncoder(ENCODER_3A, ENCODER_3B, ENCODER_3SW, -1, ENCODER_STEPS), // App 3 encoder
  AiEsp32RotaryEncoder(ENCODER_2A, ENCODER_2B, ENCODER_2SW, -1, ENCODER_STEPS), // Selecter encoder
  AiEsp32RotaryEncoder(ENCODER_1A, ENCODER_1B, ENCODER_1SW, -1, ENCODER_STEPS)  // Main volume encoder
};
#define SELECTOR_ENCODER_IDX NUM_APP_ENCODERS
#define MAIN_VOLUME_ENCODER_IDX NUM_APP_ENCODERS + 1

void setup(void) {
  initCommunication();
  initEncoders();
  initScreen();
}

void initCommunication() {
  Serial.begin(115200);
  SerialBT.begin(BT_NAME);
}

// Triggers interupt for encoders
void IRAM_ATTR readEncoderISR() {
  for (int i = 0; i < NUM_ENCODERS; i++) {
    rotaryEncoders[i].readEncoder_ISR();
  }
}

void initEncoders() {
  for (int i = 0; i < NUM_ENCODERS; i++){
    rotaryEncoders[i].begin();
    rotaryEncoders[i].setup(readEncoderISR);
    if (i != MAIN_VOLUME_ENCODER_IDX) {
      rotaryEncoders[i].setBoundaries(0, 0, false);   //minValue, maxValue, circleValues true|false (when max go to min and vice versa)
    } else {
      rotaryEncoders[i].setBoundaries(0, 100, false);   //minValue, maxValue, circleValues true|false (when max go to min and vice versa)
    }
    if (i != SELECTOR_ENCODER_IDX){
      rotaryEncoders[i].setAcceleration(75);            //larger number = more accelearation; 0 or 1 means disabled acceleration
    }
    else{
      rotaryEncoders[i].setAcceleration(0);             //larger number = more accelearation; 0 or 1 means disabled acceleration
    }
  }
}

void initScreen() {
  int xpos;
  int ypos;

  tft.begin();                                            // Initialize the TFT screen
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);
  tft.setRotation(3);                                     // Set the rotation of the screen
  tft.fillScreen(0x0000);                                 // Fill the screen with black
  tft.pushImage(0, 0, backgroundWidth, backgroundHeight, background);   // Insert background image

  // draws resource manager square
  xpos = 2;
  ypos = 2;
  tft.setFreeFont(&FreeSans12pt7b);                                                     // Select the font
  tft.fillRoundRect(xpos, ypos, 170, (ypos + (tft.fontHeight(1) * 3) + 2), 10, 0x3186); // Draw the square

  //draws main volume bar
  tft.setFreeFont(&FreeSans9pt7b);                      // Select the font
  tft.setTextColor(TFT_WHITE, 0x3186);                  // White characters on GREY background
  tft.drawString("Volume", 300, 30, 1);                 // Draw the text string in the selected GFX free font
  tft.fillRoundRect(300, 50, 150, 20, 10, 0x3186);

  // draws secondary volume bars in predifined spots.
  for (int i = 0; i < NUM_APP_ENCODERS; i++) {
    tft.fillRoundRect((APP_X_POS[i] - (VOL_BAR_WIDTH / 2)), (tft.height() - VOL_BAR_HEIGHT), VOL_BAR_WIDTH, VOL_BAR_HEIGHT, VOL_BAR_HEIGHT / 2, 0x3186);
  }

  // draws labels for resource manager
  xpos = 10;                                            // Start xpos
  ypos = 10;                                            // Start ypos
  tft.setFreeFont(&FreeSans12pt7b);                     // Select the font
  tft.setTextColor(TFT_WHITE, 0x3186);                  // White characters on GREY background
  tft.drawString("CPU:", xpos, ypos, 1);                // Draw the text string in the selected GFX free font
  ypos += tft.fontHeight(1);                            // Get the font height and move ypos down
  tft.drawString("GPU:", xpos, ypos, 1);                // Repeat textprint 2x
  ypos += tft.fontHeight(1);
  tft.drawString("RAM:", xpos, ypos, 1);
  ypos += tft.fontHeight(1);

  drawResourceStats("-", "-", "-");
  drawAppVolumes();
  drawMainVolume();
}

void loop() {
  readAndParseSerialInput();
  rotaryLoop();
}

void rotaryLoop(){
  for (int i = 0; i < NUM_ENCODERS; i++){
    if (rotaryEncoders[i].encoderChanged()){
      int encoderValue = rotaryEncoders[i].readEncoder();
      if (i != SELECTOR_ENCODER_IDX && i < numApps || i == MAIN_VOLUME_ENCODER_IDX) { // Skip index 3 (selector) and only change if apps are loaded in
        updateVolume(i, encoderValue);
        if (i != MAIN_VOLUME_ENCODER_IDX){
          sendVolumeSerial(encoderIndexToAppIndex(i), encoderValue);
        }
        else{
          sendVolumeSerial(-1, encoderValue);
        }
      }
      if(i == SELECTOR_ENCODER_IDX){
        scrollPrograms(encoderValue);
      }
    }
    if (rotaryEncoders[i].isEncoderButtonClicked()){
      onRotaryButtonClick(i);
    }
  }
}

/**
 * @param index encoder index to update 
 * @param volume new encoder volume value
 */
void updateVolume(int index, int volume) {
  if (index < NUM_APP_ENCODERS) {
    // For individual app volumes
    volumes[encoderIndexToAppIndex(index)] = volume;
    drawAppVolume(index);
  } else {
    // For main volume
    mainVolume = volume;
    drawMainVolume();
  }
}

void drawAppVolumes() {
  for (int i = 0; i < NUM_APP_ENCODERS; i++) {
    if (i < numApps) {
      rotaryEncoders[i].setEncoderValue(volumes[encoderIndexToAppIndex(i)]);
      rotaryEncoders[i].encoderChanged();
    } else {
      rotaryEncoders[i].setEncoderValue(0);
      rotaryEncoders[i].encoderChanged();
    }
    drawAppVolume(i);
  }
}

/**
 * @param index encoder index to update 
 */
void drawAppVolume(int index) {
  int volume = 0;
  if (index < numApps) {
    volume = volumes[encoderIndexToAppIndex(index)];
  }
  if (prevVolumes[index] != volume) { // Check if volume has changed
    int prevWidth = VOL_BAR_WIDTH * prevVolumes[index] * 0.01; // Previous width of the volume bar
    int newWidth = VOL_BAR_WIDTH * volume * 0.01; // New width of the volume bar
    int diffWidth = abs(newWidth - prevWidth); // Difference in width
    
    // Clear or draw volume bar based on the difference in width
    if (newWidth > prevWidth) {
      tft.fillRoundRect(APP_X_POS[index] - (VOL_BAR_WIDTH / 2), (tft.height() - VOL_BAR_HEIGHT), newWidth, VOL_BAR_HEIGHT, VOL_BAR_HEIGHT / 2, 0xffff);
    } else {
      tft.fillRect(APP_X_POS[index] - (VOL_BAR_WIDTH / 2) + newWidth, (tft.height() - VOL_BAR_HEIGHT), diffWidth, VOL_BAR_HEIGHT, 0x3186);
    }
    
    // Update previous volume
    prevVolumes[index] = volume;

    drawVolumeText(index, volume);
  }
}

void drawMainVolume() {
  int index = MAIN_VOLUME_ENCODER_IDX;
  if (prevVolumes[index] != mainVolume) { // Check if volume has changed
    int prevWidth = 150 * prevVolumes[index] * 0.01; // Previous width of the volume bar
    int newWidth = 150 * mainVolume * 0.01; // New width of the volume bar
    int diffWidth = abs(newWidth - prevWidth); // Difference in width
    
    // Clear or draw main volume bar based on the difference in width
    if (newWidth > prevWidth) {
      tft.fillRoundRect(300, 50, newWidth, 20, 10, 0xffff);
    } else {
      tft.fillRect(300 + newWidth, 50, diffWidth, 20, 0x3186);
    }
    
    // Update previous volume
    prevVolumes[index] = mainVolume;

    drawVolumeText(index, mainVolume);
  }
}

void drawVolumeText(int index, int volume) {
  // Clear the percentage display area
  tft.setFreeFont(&FreeSans9pt7b);
  int clearX = (index < NUM_APP_ENCODERS) ? APP_X_POS[index] - 7 : 390;
  int clearY = (index < NUM_APP_ENCODERS) ? ((tft.height() - VOL_BAR_HEIGHT) - tft.fontHeight(1)) : 28;
  int clearWidth = tft.textWidth("100%") + 4;
  int clearHeight = tft.fontHeight(1) - 4;
  //writeln("Drawing rect at x:" + String(clearX) + ", y:" + String(clearY) + ", w:" + String(clearWidth) + ", h:" + String(clearHeight));
  tft.fillRoundRect(clearX, clearY, clearWidth, clearHeight, 4, 0x3186);

  // Display percentage value
  char str[20];
  sprintf(str, "%d%%", volume);
  tft.setFreeFont(&FreeSans9pt7b);
  int textX = (index < NUM_APP_ENCODERS) ? APP_X_POS[index] - 5 : 390 - 5;
  int textY = (index < NUM_APP_ENCODERS) ? ((tft.height() - VOL_BAR_HEIGHT) - tft.fontHeight(1)) + 2 : 28 + 2;
  tft.drawString(str, textX, textY, 1);
}

void onRotaryButtonClick(int index){
  static unsigned long lastTimePressed = 0; // Soft debouncing
  if (millis() - lastTimePressed < 100) {
    return;
  }
  if (index < NUM_APP_ENCODERS){
    // TODO: Mute apps
  }
  lastTimePressed = millis();
}

void drawResourceStats(String cpu, String gpu, String ram){
  tft.setFreeFont(&FreeSans12pt7b);

  int ramTextWidth = tft.textWidth("RAM: ");

  int xpos = (10 + ramTextWidth);
  int ypos = 2;
  //Overwrite current data with grey
  tft.fillRoundRect(xpos, ypos, (205 - ramTextWidth), (ypos + (tft.fontHeight(1) * 3) + 2), 10, 0x3186); //3th variable is width of box

  ypos = 10;
  tft.setTextColor(TFT_WHITE, 0x3186);            // White characters on GREY background
  tft.drawString(" " + cpu, xpos, ypos, 1);       // Draw the text string in the selected GFX free font
  ypos += tft.fontHeight(1);                      // Get the font height and move ypos down
  tft.drawString(" " + gpu, xpos, ypos, 1);
  ypos += tft.fontHeight(1);
  tft.drawString(" " + ram, xpos, ypos, 1);
  ypos += tft.fontHeight(1);
}

void readAndParseSerialInput() {
  if (!Serial.available() && !SerialBT.available()) {
    return;
  }

  char separator = ',';
  String data = "";
  if (Serial.available()){
    data = Serial.readString() + separator;
  } else {
    data = SerialBT.readString() + separator;
  }

  int count = 0;
  for (int i = 0; i < data.length(); i++) {
    if (data[i] == ',') {
      count++;
    }
  }

  int nonAppFields = 4; // Number of non-app fields, currently cpu,gpu,ram,mainVolume
  if (count < nonAppFields) {
    return;
  }

  int splitIndices[count] = {0};
  int found = 0;
  splitIndices[0] = 0;
  for (int i = 0; i < data.length(); i++) {
    if (data.charAt(i) == separator) {
      splitIndices[found + 1] = i + 1;
      found++;
    }
  }

  String cpu = data.substring(splitIndices[0], splitIndices[1] - 1);
  String gpu = data.substring(splitIndices[1], splitIndices[2] - 1);
  String ram = data.substring(splitIndices[2], splitIndices[3] - 1);
  mainVolume = data.substring(splitIndices[3], splitIndices[4] - 1).toInt();

  numApps = (count - nonAppFields) / 2;
  String *localApps = new String[numApps]; // Dynamically allocate memory for app names
  apps = localApps;
  int *localVolumes = new int[numApps]; // Dynamically allocate memory for volume levels
  volumes = localVolumes;

  if (numApps <= NUM_APP_ENCODERS) {
    rotaryEncoders[SELECTOR_ENCODER_IDX].setBoundaries(0, 0, false);
    rotaryEncoders[SELECTOR_ENCODER_IDX].setEncoderValue(0);
    rotaryEncoders[SELECTOR_ENCODER_IDX].encoderChanged();
    programIndex = 0;
  } else {
    rotaryEncoders[SELECTOR_ENCODER_IDX].setBoundaries(0, numApps, true);
  }

  drawResourceStats(cpu, gpu, ram);
  drawMainVolume();

  for (int i = 0; i < numApps; i++) {
    apps[i] = data.substring(splitIndices[nonAppFields + i * 2], splitIndices[nonAppFields + 1 + i * 2] - 1);
    volumes[i] = data.substring(splitIndices[nonAppFields + 1 + i * 2], splitIndices[nonAppFields + 2 + i * 2] - 1).toInt();
  }
  for (int i = 0; i < NUM_APP_ENCODERS; i++) {
    if (i < numApps) {
      rotaryEncoders[i].setBoundaries(0, 100, false);
    } else {
      rotaryEncoders[i].setBoundaries(0, 0, false);
    }
  }
  drawAppVolumes();
  drawAppLabels(); // update apps in display
}

void sendVolumeSerial(int index, int volume){
  writeln(String(index) + "," + String(volume));
}

void scrollPrograms(int encoderValue){
  if (numApps <= NUM_APP_ENCODERS) {
    // Don't scroll if number of apps is at most equal to number of apps shown at a time
    return;
  }
  if (encoderValue >= numApps && numApps > 0){ 
    // When near the boundary, we get the value and immediately the wrapped around next value
    // Might be a bug in the library or our code but we just set the max boundary one too high 
    // and skip over the last value
    if (programIndex + 1 == numApps) {
      rotaryEncoders[SELECTOR_ENCODER_IDX].setEncoderValue(0);
      rotaryEncoders[SELECTOR_ENCODER_IDX].encoderChanged();
      encoderValue = 0;
    } else {
      return;
    }
  }
  programIndex = encoderValue;

  drawAppVolumes();
  drawAppLabels(); // update apps in display
}

void drawAppLabels() {
  int localAppsSize = max(numApps, NUM_APP_ENCODERS);
  String localApps[localAppsSize]; // Define a local array to hold app names
  for (int i = 0; i < numApps; i++) {
    localApps[i] = apps[i]; // Copy the contents of the apps pointer into the localApps array
  }
  for (int i = numApps; i < localAppsSize; i++) {
    localApps[i] = ""; // Fill the remaining spots with empty strings
  }

  int yPos = 250; // Set the y position for the text
  int clearHeight = 35; // Height of a single text line (adjust if necessary)
  
  // Clear a single horizontal bar of the background once
  int clearY = yPos - (clearHeight/2); // Centering the clearing area vertically around the text y position
  int clearWidth = backgroundWidth; // Full width of the screen

  // Extract the correct portion of the background image
  uint16_t* backgroundPart = (uint16_t*) malloc(clearWidth * clearHeight * sizeof(uint16_t));
  for (int y = 0; y < clearHeight; y++) {
    for (int x = 0; x < clearWidth; x++) {
      backgroundPart[y * clearWidth + x] = background[(clearY + y) * backgroundWidth + x];
    }
  }
  
  // Push the extracted background image onto the screen
  tft.pushImage(0, clearY, clearWidth, clearHeight, backgroundPart);

  free(backgroundPart);
  
  // Display each app name
  int currentIdx = (localAppsSize - programIndex) % localAppsSize; // Determine the starting index for displaying app names
  for (int appCount = 0; appCount < NUM_APP_ENCODERS; appCount++) {
    char* truncatedAppName = truncateText(localApps[currentIdx], 130);

    int textWidth = tft.textWidth(truncatedAppName);    // Calculate the text width
    int xPosCenter = APP_X_POS[appCount] - (textWidth / 2);   // Calculate the x position to center the text
    
    // Display the app name
    tft.setFreeFont(&FreeSans9pt7b); // Select the font
    tft.setTextColor(TFT_WHITE, 0x3186); // White characters on GREY background
    tft.drawString(truncatedAppName, xPosCenter, yPos, 1); // Draw the text string
    
    free(truncatedAppName);

    prevTextWidth[appCount] = textWidth;  // Store the previous text width for the current app spot
    currentIdx = (currentIdx + 1 + localAppsSize) % localAppsSize; // Cycle through apps
  }
}

char* truncateText(String originalText, int truncateSize) {
  int truncatedTextLength = originalText.length() + 1;
  char* truncatedText = (char*) calloc(truncatedTextLength + 1, 1);
  originalText.toCharArray(truncatedText, truncatedTextLength);

  if (truncatedTextLength < 3 || tft.textWidth(truncatedText) <= truncateSize) {
    return truncatedText;
  }

  truncatedText[truncatedTextLength - 3] = '.';
  truncatedText[truncatedTextLength - 2] = '.';
  truncatedText[truncatedTextLength - 1] = '.';
  while (tft.textWidth(truncatedText) > truncateSize && truncatedTextLength >= 4) {
    truncatedText[truncatedTextLength - 4] = '.';
    truncatedText[truncatedTextLength - 1] = 0;
    truncatedTextLength -= 1;
  }

  return truncatedText;
}

int encoderIndexToAppIndex(int encoderIndex) {
  return (encoderIndex - programIndex + numApps) % numApps;
}

void writeln(String message) {
  // Sending serial and BTserial
  Serial.println(message);
  SerialBT.println(message);
}

void write (String message) {
  // Sending serial and BTserial
  Serial.print(message);
  SerialBT.print(message);
}