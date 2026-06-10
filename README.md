# MyHome IoT - Professional IoT Home Automation Platform

A modern, production-ready Django 5 application for controlling smart home devices (ESP8266/ESP32) with a beautiful web dashboard similar to Blynk, SmartThings, and Home Assistant.

## 🚀 Features

### Core Features
- **Device Management**: Add, edit, delete, and monitor IoT devices
- **Appliance Control**: Control home appliances with instant state updates
- **Real-time Updates**: WebSocket support for live device status
- **Beautiful Dashboard**: Modern UI with Bootstrap 5 and dark mode support
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Activity Logs**: Track all device and appliance actions

### Authentication & Security
- User registration with email verification
- JWT token-based authentication
- API Key authentication for devices
- Password reset functionality
- Two-factor authentication support
- Login history tracking

### API Features
- RESTful APIs for web and mobile clients
- Device authentication endpoints
- Appliance state management APIs
- Real-time WebSocket connections
- Rate limiting and throttling
- API documentation endpoint

### Admin Dashboard
- User management (activate/deactivate)
- Device monitoring
- API call tracking
- System health overview
- Firmware version management

### Notification System
- In-app notifications
- Email notifications
- Device offline alerts
- Firmware update alerts
- Customizable notification preferences

## 📋 Requirements

- Python 3.10+
- Django 5.0+
- PostgreSQL 12+
- Redis (for WebSockets and caching)
- Node.js (optional, for static asset compilation)

## 🛠️ Installation

### 1. Clone the Repository
```bash
cd /Users/sksuman/Documents/Smart\ Iot\ Home/myhome
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Database Setup
```bash
# Install PostgreSQL and create database
psql
CREATE DATABASE myhome_db;
CREATE USER myhome_user WITH PASSWORD 'your_password';
ALTER ROLE myhome_user SET client_encoding TO 'utf8';
ALTER ROLE myhome_user SET default_transaction_isolation TO 'read_committed';
ALTER ROLE myhome_user SET default_transaction_deferrable TO on;
ALTER ROLE myhome_user SET default_transaction_level TO 'read_committed';
ALTER ROLE myhome_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE myhome_db TO myhome_user;
\\q
```

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 9. Run Development Server
```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Celery worker (if using tasks)
celery -A myhome worker -l info

# Terminal 3: Redis server
redis-server
```

Visit: http://localhost:8000

## 📱 API Documentation

### Device Authentication
```bash
POST /api/device/auth/

{
    "device_id": "ESP8266_001",
    "api_key": "your_api_key_here"
}

Response:
{
    "status": "success",
    "message": "Device authenticated successfully",
    "device_id": "ESP8266_001"
}
```

### Get Appliance States
```bash
GET /api/device/states/?api_key=YOUR_API_KEY

Response:
{
    "status": "success",
    "V0": 1,
    "V1": 0,
    "V2": 1,
    "V3": 0
}
```

### Update Device Status
```bash
POST /api/device/status/

{
    "api_key": "your_api_key",
    "device_id": "ESP8266_001",
    "temperature": 28.5,
    "humidity": 65,
    "wifi_signal": -55
}
```

### Device Heartbeat
```bash
POST /api/device/heartbeat/

{
    "api_key": "your_api_key",
    "device_id": "ESP8266_001"
}
```

### Update Appliance State
```bash
POST /api/device/appliance/state/

{
    "api_key": "your_api_key",
    "device_id": "ESP8266_001",
    "virtual_pin": "V0",
    "state": 1
}
```

### Set Appliance State (User Control)
```bash
POST /api/device/appliance/set/

{
    "api_key": "your_api_key",
    "device_id": "ESP8266_001",
    "virtual_pin": "V0",
    "state": 1
}
```

## 🔌 ESP8266/ESP32 Integration

### Arduino Example Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* serverUrl = "http://192.168.1.100:8000/api";
const char* deviceId = "ESP8266_001";
const char* apiKey = "your_api_key_here";

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\\nWiFi connected!");
    authenticate();
}

void authenticate() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/auth/";
    
    DynamicJsonDocument doc(200);
    doc["device_id"] = deviceId;
    doc["api_key"] = apiKey;
    
    String payload;
    serializeJson(doc, payload);
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    int httpCode = http.POST(payload);
    
    if (httpCode == 200) {
        Serial.println("Device authenticated successfully!");
    }
    
    http.end();
}

void getStates() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/states/?api_key=" + String(apiKey);
    
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String response = http.getString();
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, response);
        
        // Parse states
        int v0 = doc["V0"];
        int v1 = doc["V1"];
        // ... apply states to GPIO pins
    }
    
    http.end();
}

void updateStatus() {
    HTTPClient http;
    String url = String(serverUrl) + "/device/status/";
    
    DynamicJsonDocument doc(256);
    doc["api_key"] = apiKey;
    doc["device_id"] = deviceId;
    doc["temperature"] = readTemperature();
    doc["humidity"] = readHumidity();
    doc["wifi_signal"] = WiFi.RSSI();
    
    String payload;
    serializeJson(doc, payload);
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.POST(payload);
    http.end();
}

void loop() {
    getStates();
    updateStatus();
    delay(5000); // Update every 5 seconds
}
```

## 🏗️ Project Structure

```
myhome/
├── myhome/                 # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI config
│   └── asgi.py            # ASGI config (WebSockets)
│
├── accounts/              # User authentication
│   ├── models.py          # User, APIKey models
│   ├── views.py           # Auth views
│   ├── serializers.py     # DRF serializers
│   └── urls.py            # Auth URLs
│
├── devices/               # Device management
│   ├── models.py          # Device, Appliance models
│   ├── views.py           # Device views
│   ├── serializers.py     # Device serializers
│   └── urls.py            # Device URLs
│
├── api/                   # REST APIs for devices
│   ├── views.py           # API endpoints
│   └── urls.py            # API URLs
│
├── dashboard/             # Web dashboard
│   ├── views.py           # Dashboard views
│   └── urls.py            # Dashboard URLs
│
├── notifications/         # Notification system
│   ├── models.py          # Notification models
│   ├── views.py           # Notification views
│   └── urls.py            # Notification URLs
│
├── websocket/             # WebSocket consumers
│   ├── consumers.py       # Channels consumers
│   └── routing.py         # WebSocket routing
│
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── dashboard/         # Dashboard templates
│   └── accounts/          # Auth templates
│
├── static/                # Static files
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript
│   └── images/            # Images
│
├── requirements.txt       # Python dependencies
├── manage.py              # Django management
└── README.md              # This file
```

## 🗄️ Database Models

### User Model
- Extended Django User with role (admin/user)
- Profile image, bio, theme preference
- Email verification status
- API keys management

### Device Model
- Device ID (unique identifier)
- API Key (for authentication)
- Status (online/offline/inactive)
- Firmware version
- Environmental data (temperature, humidity, WiFi signal)
- Last seen timestamp

### Appliance Model
- Name and description
- Virtual pin (V0, V1, etc.)
- Current state (0=OFF, 1=ON)
- Room/location
- Power consumption tracking
- Control restrictions

### Appliance History
- Previous and new states
- Action type (turned_on, turned_off, etc.)
- Who triggered the action (user/automation/device)
- Timestamp
- Duration on

### Notification
- Title and message
- Notification type
- Related device/appliance
- Read status
- Action URL

## 🔐 Security Features

- **JWT Authentication**: Secure token-based API access
- **API Keys**: Device authentication
- **CSRF Protection**: Django CSRF middleware
- **Rate Limiting**: API request throttling
- **SQL Injection Prevention**: Django ORM
- **XSS Protection**: Template escaping
- **Secure Headers**: HTTPS, HSTS, X-Frame-Options
- **Password Hashing**: Django password hasher
- **Email Verification**: Confirm user email
- **Login Logging**: Track login attempts

## 🚀 Deployment

### Production Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn myhome.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Run Daphne for WebSockets
daphne -b 0.0.0.0 -p 8001 myhome.asgi:application
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "myhome.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Nginx Configuration

```nginx
upstream myhome {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://myhome;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /app/staticfiles;
    }
}
```

## 📊 Admin Dashboard

Access the admin dashboard at: `http://localhost:8000/admin`

Features:
- User management (create, edit, deactivate)
- Device monitoring and control
- API key generation and revocation
- Activity log review
- Notification management
- Firmware version uploads
- System statistics

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Run specific test
python manage.py test accounts.tests.UserTests
```

## 📚 Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Bootstrap 5](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)

## 🔗 Useful Commands

```bash
# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Clear cache
python manage.py clear_cache

# Flush database (CAUTION!)
python manage.py flush
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👨‍💻 Author

MyHome IoT Platform - Professional IoT Home Automation

## 🙏 Acknowledgments

- Django community
- Django REST Framework
- Bootstrap team
- Font Awesome

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Happy Smart Home Automating! 🏠💡**
