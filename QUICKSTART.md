# QUICK START GUIDE

## 🚀 Quick Start - Choose Your Path

### Option 1: cPanel Hosting (Shared Hosting) ⭐ EASIEST

Follow **[CPANEL_SETUP.md](CPANEL_SETUP.md)** for complete cPanel hosting setup.

Summary:
```bash
1. Create database in cPanel
2. Upload files via SFTP
3. SSH - create virtual environment
4. Install packages: pip install -r requirements.txt
5. Configure .env with database credentials
6. Run migrations: python manage.py migrate
7. Create superuser: python manage.py createsuperuser
8. Set up web server in cPanel
9. Access at https://yourdomain.com
```

### Option 2: Using Docker (Local/Advanced)

```bash
# Clone/enter directory
cd /Users/sksuman/Documents/Smart\ Iot\ Home/myhome

# Create .env file
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Visit
open http://localhost
```

### Option 3: Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env
cp .env.example .env

# Setup database (PostgreSQL must be running)
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## 📝 First Steps

1. **Login**
   - Go to http://localhost:8000/accounts/login/
   - Or register at http://localhost:8000/accounts/register/

2. **Add Device**
    - Go to Devices page
    - Click "Add Device"
    - Fill in Device ID and Device Name only
    - The system uses the shared registration API key from your account
    - Open your Profile page to copy the API key, then add appliances to the device

3. **Configure Device Code**
   - Use ESP8266/ESP32 code (see API_DOCUMENTATION.md)
   - Update SSID, password, API key, device ID

4. **Add Appliances**
    - Go to the device details page for the device you created
    - Add appliances using virtual pins like V0, V1, V2
    - All appliances under every device use the same shared account API key

5. **Control from Dashboard**
   - Toggle appliances from dashboard
   - View real-time status
   - Check activity logs

## 🔑 Useful Links

- Dashboard: http://localhost:8000/dashboard/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/
- API Devices: http://localhost:8000/api/device/

## 🛠️ Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

# Stop and remove Docker containers
docker-compose down

# View logs
docker-compose logs -f web

# Access Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic --noinput
```

## 🔐 Default Credentials (Development Only)

After running `python manage.py createsuperuser`, use those credentials.

## 📱 Device Setup

### ESP8266 Arduino Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://192.168.1.100:8000/api";  // Your server IP
const char* deviceId = "ESP8266_001";
const char* apiKey = "your_device_api_key";

// Pins
const int pin_V0 = D1;  // GPIO5
const int pin_V1 = D2;  // GPIO4
const int pin_V2 = D3;  // GPIO0
const int pin_V3 = D4;  // GPIO2
const int pin_V4 = D5;  // GPIO14
const int pin_V5 = D6;  // GPIO12
const int pin_V6 = D7;  // GPIO13
const int pin_V7 = D8;  // GPIO15

void setup() {
    Serial.begin(115200);
    
    // Initialize pins
    pinMode(pin_V0, OUTPUT);
    pinMode(pin_V1, OUTPUT);
    pinMode(pin_V2, OUTPUT);
    pinMode(pin_V3, OUTPUT);
    pinMode(pin_V4, OUTPUT);
    pinMode(pin_V5, OUTPUT);
    pinMode(pin_V6, OUTPUT);
    pinMode(pin_V7, OUTPUT);
    
    // Connect WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\\nWiFi connected!");
    
    // Authenticate
    authenticateDevice();
}

void loop() {
    // Get states every 5 seconds
    getAndApplyStates();
    
    // Send status every 30 seconds
    if (millis() % 30000 == 0) {
        sendStatus();
    }
    
    delay(5000);
}

void authenticateDevice() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/auth/";
    
    DynamicJsonDocument doc(200);
    doc["device_id"] = deviceId;
    doc["api_key"] = apiKey;
    
    String payload;
    serializeJson(doc, payload);
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(payload);
    
    Serial.print("Auth response: ");
    Serial.println(code);
    http.end();
}

void getAndApplyStates() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/states/?api_key=" + String(apiKey) + "&device_id=" + String(deviceId);
    
    http.begin(url);
    int code = http.GET();
    
    if (code == 200) {
        String response = http.getString();
        DynamicJsonDocument doc(512);
        deserializeJson(doc, response);
        
        // Apply states to GPIO pins
        digitalWrite(pin_V0, doc["V0"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V1, doc["V1"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V2, doc["V2"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V3, doc["V3"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V4, doc["V4"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V5, doc["V5"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V6, doc["V6"] == 1 ? HIGH : LOW);
        digitalWrite(pin_V7, doc["V7"] == 1 ? HIGH : LOW);
        
        Serial.println("States applied");
    }
    http.end();
}

void sendStatus() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/status/";
    
    DynamicJsonDocument doc(300);
    doc["api_key"] = apiKey;
    doc["device_id"] = deviceId;
    doc["temperature"] = 25.5;  // Read from sensor
    doc["humidity"] = 60;        // Read from sensor
    doc["wifi_signal"] = WiFi.RSSI();
    
    String payload;
    serializeJson(doc, payload);
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(payload);
    
    Serial.print("Status update: ");
    Serial.println(code);
    http.end();
}
```

## 🆘 Troubleshooting

### Docker containers won't start
```bash
# Check logs
docker-compose logs

# Clean up and restart
docker-compose down -v
docker-compose up -d
```

### Database connection error
```bash
# Check if PostgreSQL is running (for local setup)
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Ensure .env has correct database settings
```

### WebSocket connection issues
```bash
# Check Redis is running
redis-cli ping

# Verify WebSocket URL
# Should be ws:// or wss:// (not http://)
```

### Can't login after setup
```bash
# Create new superuser
python manage.py createsuperuser

# Reset password
python manage.py changepassword username
```

## 📞 Need Help?

- Check README.md for detailed documentation
- See API_DOCUMENTATION.md for API details
- See DEPLOYMENT.md for production setup
- Check logs: `docker-compose logs web`

---

**Ready to control your home! 🏠💡**
