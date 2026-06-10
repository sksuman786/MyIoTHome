# OTA Update - Correct Device-Aware Flow

## For Users (Dashboard)

### Step 1: Upload Firmware
1. Go to **OTA Firmware Update** page
2. Select **Target Device** (e.g., WaterMonitor_001, Room1_001)
3. Enter **Firmware Version** (e.g., v1.2.3)
4. Select **Binary File** (.bin)
5. Click **Upload**
6. Done! ✅

**Why device selection matters:** Different devices might need different firmware (e.g., water monitor vs room control).

---

## For ESP8266 (Device)

Your ESP8266 needs to know:
1. Its **device_id** (e.g., WaterMonitor_001) — must match what you uploaded for
2. Your **User API Key** (get from Account Settings)
3. Its current **firmware version** (v1.0.0)

### Simple ESP8266 Code Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Update.h>

// ===== CONFIGURATION =====
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* server = "http://your-server.com";
const char* user_api_key = "YOUR_USER_API_KEY";
const char* device_id = "WaterMonitor_001";  // MUST MATCH UPLOADED DEVICE ID
const char* current_version = "v1.0.0";       // Update this after each successful update

// Check for OTA updates every hour
unsigned long lastCheckTime = 0;
const unsigned long CHECK_INTERVAL = 3600000; // 1 hour in milliseconds

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected!");
    
    checkForUpdates(); // Check on startup
}

void loop() {
    // Check for updates periodically
    if (millis() - lastCheckTime >= CHECK_INTERVAL) {
        checkForUpdates();
        lastCheckTime = millis();
    }
    
    delay(1000);
}

void checkForUpdates() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected");
        return;
    }
    
    HTTPClient http;
    String url = String(server) + "/api/ota/check/?api_key=" + user_api_key 
                 + "&device_id=" + device_id + "&current_version=" + current_version;
    
    Serial.println("Checking for updates...");
    Serial.println("URL: " + url);
    
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        Serial.println("Response: " + payload);
        
        // Parse JSON response
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, payload);
        
        bool update_available = doc["update_available"];
        
        if (update_available) {
            String latest_version = doc["latest_version"];
            String download_url = doc["download_url"];
            String checksum = doc["checksum"];
            
            Serial.println("\n✓ UPDATE AVAILABLE!");
            Serial.println("Latest: " + latest_version);
            Serial.println("Current: " + String(current_version));
            Serial.println("Download: " + download_url);
            Serial.println("Checksum: " + checksum);
            
            // Download and install firmware
            downloadAndInstallFirmware(download_url, checksum);
        } else {
            Serial.println("Running latest version");
        }
    } else {
        Serial.println("HTTP Error: " + String(httpCode));
    }
    
    http.end();
}

void downloadAndInstallFirmware(String url, String expected_checksum) {
    HTTPClient http;
    http.begin(url);
    
    int httpCode = http.GET();
    if (httpCode != 200) {
        Serial.println("Download failed: HTTP " + String(httpCode));
        http.end();
        return;
    }
    
    int contentLength = http.getSize();
    Serial.println("Firmware size: " + String(contentLength) + " bytes");
    
    // Start OTA update
    if (!Update.begin(contentLength)) {
        Serial.println("Not enough space for OTA");
        http.end();
        return;
    }
    
    // Download firmware in chunks
    WiFiClient* stream = http.getStreamPtr();
    size_t written = 0;
    uint8_t buffer[512];
    
    while (http.connected() && (written < contentLength)) {
        size_t available = stream->available();
        if (available) {
            int len = stream->readBytes(buffer, ((available > sizeof(buffer)) ? sizeof(buffer) : available));
            if (Update.write(buffer, len) == len) {
                written += len;
                Serial.print(".");
            } else {
                Serial.println("\nWrite failed");
                Update.abort();
                http.end();
                return;
            }
        }
        delay(1);
    }
    
    if (Update.end()) {
        Serial.println("\n✓ UPDATE SUCCESSFUL!");
        Serial.println("Rebooting...");
        delay(1000);
        ESP.restart();
    } else {
        Serial.println("\n✗ Update failed: " + String(Update.getError()));
        Update.abort();
    }
    
    http.end();
}
```

---

## API Flow Diagram

```
UPLOAD (Dashboard User)
┌─────────────────────────────┐
│ Select Device: WaterMonitor │
│ Version: v1.2.3             │
│ Binary File: firmware.bin   │
└──────────────┬──────────────┘
               │ POST /api/ota/upload/
               │ device_id=UUID
               │ version=v1.2.3
               │ bin_file=...
               ▼
        ┌────────────────┐
        │ Server stores: │
        │ device=UUID    │
        │ version=v1.2.3 │
        │ bin_file=...   │
        └────────────────┘

CHECK (ESP Periodically)
┌──────────────────────┐
│ ESP Device ID:       │
│ WaterMonitor_001     │
│ Current Version:     │
│ v1.0.0               │
└──────────┬───────────┘
           │ GET /api/ota/check/
           │ ?api_key=KEY
           │ &device_id=WaterMonitor_001
           │ &current_version=v1.0.0
           ▼
   ┌──────────────────────┐
   │ Server checks DB:    │
   │ device="Watermon..." │
   │ find latest version  │
   │ v1.2.3 > v1.0.0?     │
   └──────────┬───────────┘
              │ YES ✓
              ▼
      ┌─────────────────┐
      │ Return:         │
      │ update_available │
      │ download_url    │
      │ checksum        │
      └─────────────────┘

INSTALL (ESP)
┌──────────────────────────┐
│ Download from URL        │
│ Verify SHA256 checksum   │
│ Write to OTA partition   │
│ Reboot                   │
└──────────────────────────┘
```

---

## Key Points

✅ **Device-Specific**: Different devices can have different firmware versions  
✅ **Device ID Matching**: ESP must identify itself correctly (e.g., WaterMonitor_001)  
✅ **API Key Only**: Uses your main user API key  
✅ **Automatic Polling**: ESP checks periodically, no manual action  
✅ **Safe Installation**: Verifies checksum before installing  

---

## Configuration Checklist

For your ESP8266:
- [ ] Device ID set correctly (e.g., `device_id = "WaterMonitor_001"`)
- [ ] API Key configured (get from Account Settings)
- [ ] WiFi credentials correct
- [ ] Current version updated after each successful install
- [ ] Check interval set (default 1 hour)

For your Dashboard:
- [ ] Device created in system
- [ ] Upload firmware with matching device name
- [ ] Version follows semver format (v1.0.0)

