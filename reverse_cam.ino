#include "Wire.h"
#include <Preferences.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLE2902.h>

// ==========================================
// CONFIGURATION & SETTINGS
// ==========================================
// Hardware Pins
const int I2C_SDA_PIN = 21;
const int I2C_SCL_PIN = 22;
const int BUZZER_PIN  = 33;

// Preferences flash storage handle
Preferences prefs;

// Buzzer Volume as percentage (0 = silent, 100 = max) — modifiable via BLE
int buzzerVolume = 8;  // 8% — noticeably quieter

// Sensor I2C Address
#define SENSOR_ADDRESS 0x74

// Distance Thresholds (in millimeters) — modifiable via BLE
int DISTANCE_MAX_WARNING = 800;  // Start beeping 
int DISTANCE_MID_ZONE    = 400;  // Mid zone 
int DISTANCE_CLOSE_ZONE  = 150;  // Close zone 
int DISTANCE_SOLID_TONE  = 30;   // Solid tone at 3cm

// Beep Intervals per Zone (in milliseconds) — modifiable via BLE
int BEEP_FAR   = 600;  // Far zone:   slow
int BEEP_MID   = 300;  // Mid zone:   moderate
int BEEP_CLOSE = 100;  // Close zone: rapid
// ==========================================


// State Variables
uint8_t buf[2] = { 0 };
uint8_t dat = 0xB0;
int distance = 0;

// Buzzer & Sensor Timer Variables
unsigned long previousMillis = 0;
unsigned long lastSensorPoll = 0;
const unsigned long SENSOR_INTERVAL = 60; // ms between distance readings
bool buzzerState = LOW;

// ==========================================
// BLE CONFIGURATION
// ==========================================
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define SETTINGS_CHAR_UUID  "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define DISTANCE_CHAR_UUID  "1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e"

BLECharacteristic *pSettingsChar = nullptr;
BLECharacteristic *pDistanceChar = nullptr;
bool deviceConnected = false;

// Builds a CSV string of all current settings
String buildSettingsCSV() {
  return String(DISTANCE_MAX_WARNING) + "," + String(DISTANCE_MID_ZONE) + "," +
         String(DISTANCE_CLOSE_ZONE) + "," + String(DISTANCE_SOLID_TONE) + "," +
         String(BEEP_FAR) + "," + String(BEEP_MID) + "," + String(BEEP_CLOSE) + "," +
         String(buzzerVolume);
}

// Loads calibration thresholds from non-volatile flash memory
void loadSettings() {
  prefs.begin("revcam", true); // Read-only
  DISTANCE_MAX_WARNING = prefs.getInt("max_warn", 800);
  DISTANCE_MID_ZONE    = prefs.getInt("mid_zone", 400);
  DISTANCE_CLOSE_ZONE  = prefs.getInt("close_zone", 150);
  DISTANCE_SOLID_TONE  = prefs.getInt("solid_tone", 30);
  BEEP_FAR             = prefs.getInt("beep_far", 600);
  BEEP_MID             = prefs.getInt("beep_mid", 300);
  BEEP_CLOSE           = prefs.getInt("beep_close", 100);
  buzzerVolume         = prefs.getInt("volume", 8);
  prefs.end();
  Serial.println("NVS: Settings loaded from flash: " + buildSettingsCSV());
}

// Persists calibration thresholds to non-volatile flash memory
void saveSettings() {
  prefs.begin("revcam", false); // Read-write
  prefs.putInt("max_warn", DISTANCE_MAX_WARNING);
  prefs.putInt("mid_zone", DISTANCE_MID_ZONE);
  prefs.putInt("close_zone", DISTANCE_CLOSE_ZONE);
  prefs.putInt("solid_tone", DISTANCE_SOLID_TONE);
  prefs.putInt("beep_far", BEEP_FAR);
  prefs.putInt("beep_mid", BEEP_MID);
  prefs.putInt("beep_close", BEEP_CLOSE);
  prefs.putInt("volume", buzzerVolume);
  prefs.end();
  Serial.println("NVS: Settings persisted to flash.");
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    deviceConnected = true;
    Serial.println("BLE: Client connected");
  }
  void onDisconnect(BLEServer* pServer) override {
    deviceConnected = false;
    Serial.println("BLE: Client disconnected");
    BLEDevice::startAdvertising();
  }
};

class SettingsCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) override {
    String value = String(pCharacteristic->getValue().c_str());
    if (value.length() == 0) return;

    // Parse CSV: "800,400,150,30,600,300,100,8"
    int parsed[8];
    int idx = 0;
    int startPos = 0;
    for (unsigned int i = 0; i <= value.length() && idx < 8; i++) {
      if (i == value.length() || value.charAt(i) == ',') {
        parsed[idx++] = value.substring(startPos, i).toInt();
        startPos = i + 1;
      }
    }

    if (idx == 8) {
      DISTANCE_MAX_WARNING = parsed[0];
      DISTANCE_MID_ZONE    = parsed[1];
      DISTANCE_CLOSE_ZONE  = parsed[2];
      DISTANCE_SOLID_TONE  = parsed[3];
      BEEP_FAR             = parsed[4];
      BEEP_MID             = parsed[5];
      BEEP_CLOSE           = parsed[6];
      buzzerVolume         = constrain(parsed[7], 0, 100);

      // Persist across vehicle power cycles
      saveSettings();

      String csv = buildSettingsCSV();
      pSettingsChar->setValue(csv.c_str());
      Serial.println("BLE: Settings updated — " + csv);
    } else {
      Serial.println("BLE: Invalid format (expected 8 CSV values)");
    }
  }
};


void setup() {
  Serial.begin(115200);
  
  // Load persisted calibration settings from flash
  loadSettings();

  // Initialize Buzzer PWM (LEDC)
  ledcAttach(BUZZER_PIN, 2000, 8);  // 2 kHz frequency, 8-bit resolution (0–255)
  ledcWrite(BUZZER_PIN, 0);         // Ensure buzzer is off on boot
  
  // Initialize I2C
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  // Initialize BLE
  BLEDevice::init("ReverseCam");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Settings characteristic (Read + Write)
  pSettingsChar = pService->createCharacteristic(
    SETTINGS_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE
  );
  pSettingsChar->setCallbacks(new SettingsCallbacks());
  pSettingsChar->setValue(buildSettingsCSV().c_str());

  // Distance characteristic (Read + Notify)
  pDistanceChar = pService->createCharacteristic(
    DISTANCE_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pDistanceChar->addDescriptor(new BLE2902());

  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("BLE: Advertising as 'ReverseCam'");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Non-blocking sensor polling interval
  if (currentMillis - lastSensorPoll >= SENSOR_INTERVAL) {
    lastSensorPoll = currentMillis;

    // Trigger reading & read sensor registers
    writeReg(0x10, &dat, 1);
    readReg(0x02, buf, 2);
    distance = buf[0] * 0x100 + buf[1] + 10;

    // Output to Serial Monitor for debugging
    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" mm");

    // Update BLE distance (if connected)
    if (deviceConnected) {
      pDistanceChar->setValue(String(distance).c_str());
      pDistanceChar->notify();
    }
  }

  // 2. Process the Buzzer Logic with precise non-blocking timing
  handleBuzzer(distance);
}

// ==========================================
// MODULAR FUNCTIONS
// ==========================================

void handleBuzzer(int currentDistance) {
  // Out of range or invalid reading — buzzer off
  if (currentDistance > DISTANCE_MAX_WARNING || currentDistance <= 0) {
    ledcWrite(BUZZER_PIN, 0);
    buzzerState = LOW;
    return;
  }
  
  // Extremely close — solid continuous tone
  if (currentDistance <= DISTANCE_SOLID_TONE) {
    ledcWrite(BUZZER_PIN, map(buzzerVolume, 0, 100, 0, 255));
    buzzerState = HIGH;
    return;
  }
  
  // Determine which zone we're in and pick the beep interval
  int beepInterval;
  if (currentDistance <= DISTANCE_CLOSE_ZONE) {
    beepInterval = BEEP_CLOSE;  // 150mm – 30mm  → rapid beeps
  } else if (currentDistance <= DISTANCE_MID_ZONE) {
    beepInterval = BEEP_MID;    // 400mm – 150mm → moderate beeps
  } else {
    beepInterval = BEEP_FAR;    // 800mm – 400mm → slow beeps
  }
  
  unsigned long currentMillis = millis();
  
  // Toggle buzzer on/off at the zone's beep interval
  if (currentMillis - previousMillis >= (unsigned long)beepInterval) {
    previousMillis = currentMillis;
    buzzerState = !buzzerState;
    ledcWrite(BUZZER_PIN, buzzerState ? map(buzzerVolume, 0, 100, 0, 255) : 0);
  }
}

uint8_t readReg(uint8_t reg, const void* pBuf, size_t size) {
  if (pBuf == NULL) {
    return 0; 
  }
  
  uint8_t* _pBuf = (uint8_t*)pBuf;
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(reg); 
  
  if (Wire.endTransmission() != 0) {
    return 0;
  }
  delay(20);
  Wire.requestFrom((uint16_t)SENSOR_ADDRESS, (uint8_t)size); // Cast to fix potential warnings
  for (uint16_t i = 0; i < size; i++) {
    if (Wire.available()) {
        _pBuf[i] = Wire.read();
    }
  }
  return size;
}

bool writeReg(uint8_t reg, const void* pBuf, size_t size) {
  if (pBuf == NULL) {
    return 0; 
  }
  
  uint8_t* _pBuf = (uint8_t*)pBuf;
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(reg); 

  for (uint16_t i = 0; i < size; i++) {
    Wire.write(_pBuf[i]);
  }
  
  if (Wire.endTransmission() != 0) {
    return 0;
  } else {
    return 1;
  }
}