# API Documentation

## Authentication

All API endpoints require authentication via JWT token or API Key.

### JWT Token (User)
```bash
# Login
curl -X POST http://localhost:8000/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}

# Use in requests
curl -X GET http://localhost:8000/devices/devices/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### API Key (Device)
```bash
curl -X GET http://localhost:8000/api/device/states/ \
  -H "X-API-Key: your_api_key_here"
```

## Device Endpoints

### Authenticate Device
```bash
POST /api/device/auth/

Request:
{
  "device_id": "ESP8266_001",
  "api_key": "your_device_api_key"
}

Response (200):
{
  "status": "success",
  "message": "Device authenticated successfully",
  "device_id": "ESP8266_001",
  "device_name": "Living Room Control"
}
```

### Get Appliance States
```bash
GET /api/device/states/?api_key=YOUR_API_KEY&device_id=ESP8266_001

Response (200):
{
  "status": "success",
  "V0": 1,
  "V1": 0,
  "V2": 1,
  "V3": 0,
  "V4": 1,
  "V5": 0,
  "V6": 1,
  "V7": 0
}
```

### Update Device Status
```bash
POST /api/device/status/

Request:
{
  "api_key": "your_device_api_key",
  "device_id": "ESP8266_001",
  "wifi_signal": -55,
  "wifi_quality": 75,
  "uptime": 3600,
  "free_memory": 15000,
  "power_consumption": 2.5
}

Response (200):
{
  "status": "success",
  "message": "Status updated successfully",
  "device_id": "ESP8266_001"
}
```

### Device Heartbeat
```bash
POST /api/device/heartbeat/

Request:
{
  "api_key": "your_device_api_key",
  "device_id": "ESP8266_001"
}

Response (200):
{
  "status": "success",
  "message": "Heartbeat received"
}
```

### Update Appliance State (Device)
```bash
POST /api/device/appliance/state/

Request:
{
  "api_key": "your_device_api_key",
  "device_id": "ESP8266_001",
  "virtual_pin": "V0",
  "state": 1
}

Response (200):
{
  "status": "success",
  "message": "Appliance state updated",
  "virtual_pin": "V0",
  "state": 1
}
```

### Set Appliance State (User)
```bash
POST /api/device/appliance/set/

Request:
{
  "api_key": "your_user_api_key",
  "device_id": "ESP8266_001",
  "virtual_pin": "V0",
  "state": 1
}

Response (200):
{
  "status": "success",
  "message": "Appliance state set successfully",
  "virtual_pin": "V0",
  "state": 1
}
```

## Device Management Endpoints

### List Devices
```bash
GET /devices/devices/

Response (200):
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "device_id": "ESP8266_001",
      "device_name": "Living Room",
      "status": "online",
      "wifi_signal": -55,
      "is_online": true,
      "appliances": [...]
    }
  ]
}
```

## Water Monitoring API

This section documents the two different `device_id` usages:

- `device_id` in `/api/device/*` endpoints is the device hardware identifier string, e.g. `WaterMonitor_001`.
- `device_id` in dashboard/user endpoints is the Device model UUID, e.g. `dafe6aba-a392-4c9e-bcab-c39c6b8eb416`.
- The water monitoring dashboard only discovers devices with `device_role='water_monitor'`.
- Use a dedicated water monitoring device ID, not a room device ID like `Room1_001`.

Device (ESP) endpoints
- POST `/api/device/water/data/`
  - Purpose: Device submits a single water telemetry sample.
  - Auth: provide `api_key` in the JSON body (device API key).
  - Request JSON:
    {
      "api_key": "your_device_api_key",
      "device_id": "WaterMonitor_001",
      "water_percentage": 75.5,
      "tds": 450,
      "ph": 7.2,
      "temperature": 28.5,
      "timestamp": "2026-06-09T12:34:56Z"
    }
  - Success Response (200):
    {
      "status": "success",
      "message": "Water data saved successfully",
      "data": {
        "id": "uuid",
        "water_percentage": 75.5,
        "tds": 450,
        "ph": 7.2,
        "temperature": 28.5,
        "timestamp": "2026-06-09T12:34:56Z"
      }
    }
  - Errors: 400 for missing fields, 401 for invalid `api_key`.

- GET `/api/device/water/data/get/`
  - Purpose: Device or server-side tools can fetch recent water samples.
  - Query params:
    - `api_key` (device authentication) OR authenticated user
    - `device_id` (hardware string for device auth; UUID for user auth)
    - `limit` (optional)
  - Example device call: `GET /api/device/water/data/get/?api_key=KEY&device_id=WaterMonitor_001&limit=20`
  - Success Response (200): `{ "status": "success", "data": [ {record}, ... ] }`.

Pump timer & control (server API)
- POST `/api/water/pump/timer/`
  - Purpose: Create or update a pump timer for a device (user/dashboard action).
  - Auth: User authentication required (session/JWT).
  - Request JSON:
    {
      "device_id": "dafe6aba-a392-4c9e-bcab-c39c6b8eb416",
      "hours": 0,
      "minutes": 30,
      "seconds": 0,
      "is_active": true
    }
  - Success Response (200): includes `timer` object with `hours`, `minutes`, `seconds`, `total_seconds`, `is_active`, `is_running`.
  - Note: If a timer is already running, creating/updating is rejected with 400.

- GET `/api/water/pump/timer/get/?device_id=...`
  - Purpose: Retrieve timer configuration and `remaining_seconds` for a device (user auth required).
  - Use the UUID device ID here.

Device-facing pump endpoints (for ESP polling)
- POST `/api/device/water/pump/start/`
  - Purpose: Device requests to start the configured timer.
  - Auth: `api_key` in JSON body required.
  - Request JSON: `{ "api_key": "KEY", "device_id": "WaterMonitor_001" }`
  - Success Response: includes `hours`, `minutes`, `seconds`, `total_seconds`, `remaining_seconds`.

- GET `/api/device/water/pump/timer/status/?api_key=KEY&device_id=WaterMonitor_001`
  - Purpose: Device polls for current timer state (remaining seconds, is_running, started_at).
  - Success Response: `{ "status": "success", "timer": { ... } }` or 404 if not configured.

OTA Update API (Device-Specific)
- POST `/api/ota/upload/`
  - Purpose: Upload a new OTA firmware package for a specific device.
  - Auth: User authentication required (session/JWT).
  - Request: multipart/form-data with:
      - `device_id`: UUID of the target device (required)
      - `version`: firmware version string (e.g. "v1.2.3") (required)
      - `bin_file`: firmware binary file (.bin) (required)
      - `notes`: optional release notes
  - Success Response (200):
    {
      "status": "success",
      "message": "OTA update uploaded successfully",
      "update": {
        "id": "uuid",
        "version": "v1.2.3",
        "file_size": 1234567,
        "checksum": "sha256hash",
        "status": "pending"
      }
    }

- GET `/api/ota/check/?api_key=USER_API_KEY&device_id=WaterMonitor_001&current_version=v1.0.0`
  - Purpose: ESP8266 checks for firmware updates for its specific device.
  - Auth: `api_key` (user's API key) required in query params.
  - Query params:
    - `api_key`: your user API key
    - `device_id`: your device's hardware ID (e.g. "WaterMonitor_001", "Room1_001")
    - `current_version`: ESP's current firmware version (e.g. "v1.0.0")
  - Success Response if update available (200):
    {
      "status": "success",
      "update_available": true,
      "latest_version": "v1.2.3",
      "download_url": "https://.../media/ota_updates/firmware.bin",
      "file_size": 1234567,
      "checksum": "sha256hash",
      "update_id": "uuid"
    }
  - Success Response if no update (200):
    {
      "status": "success",
      "update_available": false,
      "message": "You are running the latest version"
    }

OTA Workflow for ESP8266
1. User uploads firmware via dashboard:
   - Select Target Device (e.g., WaterMonitor_001)
   - Enter Version (e.g., v1.2.3)
   - Upload Binary File

2. ESP8266 periodically checks:
   ```
   GET /api/ota/check/?api_key=KEY&device_id=WaterMonitor_001&current_version=v1.0.0
   ```

3. If update_available=true:
   - Download firmware from download_url
   - Verify SHA256 checksum
   - Install and reboot

4. Next check returns update_available=false (already on latest version)

Dashboard/browser (user) endpoints
- POST `/dashboard/api/water/pump/toggle/`
  - Purpose: Toggle pump ON/OFF from the dashboard UI.
  - Auth: User must be logged in (session or JWT).
  - Request JSON: `{ "device_id": "dafe6aba-a392-4c9e-bcab-c39c6b8eb416", "state": 1 }` (1 = ON, 0 = OFF)

- POST `/dashboard/api/water/pump/start/`
  - Purpose: Start the configured timer from the dashboard (user action). Returns the timer `total_seconds` and `remaining_seconds` for the UI.
  - Use the UUID device ID here.

- POST `/dashboard/api/water/pump/stop/`
  - Purpose: Force-stop any running timer from the dashboard.
  - Use the UUID device ID here.

- POST `/dashboard/api/water/pump/start/`
  - Purpose: Start the configured timer from the dashboard (user action). Returns the timer `total_seconds` and `remaining_seconds` for the UI.

- POST `/dashboard/api/water/pump/stop/`
  - Purpose: Force-stop any running timer from the dashboard.

Notes & tips
- Use the device API (`/api/device/*`) for firmware/ESP implementations. Provide the account's device API key in the `api_key` field.
- Use the dashboard endpoints (`/dashboard/api/*`) from browser UI code (these require the user to be authenticated).
- For exact field names and behavior refer to the handlers in `api/urls.py` and `dashboard/urls.py` (server routes). The canonical device endpoints are under `/api/` and dashboard endpoints under `/dashboard/api/`.


### Create Device
```bash
POST /devices/devices/

Request:
{
  "device_id": "ESP8266_002",
  "device_name": "Bedroom",
  "device_type": "esp8266",
  "location": "Master Bedroom"
}

Response (201):
{
  "id": "uuid",
  "device_id": "ESP8266_002",
  "device_name": "Bedroom",
  "api_key": "generated_api_key",
  ...
}
```

### Get Device Details
```bash
GET /devices/devices/{device_id}/

Response (200):
{
  "id": "uuid",
  "device_id": "ESP8266_001",
  "device_name": "Living Room",
  "appliances": [
    {
      "id": "uuid",
      "name": "Main Light",
      "virtual_pin": "V0",
      "state": 1,
      "icon": "fa-lightbulb",
      "room": "Living Room"
    }
  ],
  ...
}
```

### Update Device
```bash
PATCH /devices/devices/{device_id}/

Request:
{
  "device_name": "Living Room Updated",
  "location": "Main Living Area"
}

Response (200):
{...updated device...}
```

### Delete Device
```bash
DELETE /devices/devices/{device_id}/

Response (204): No Content
```

## Appliance Endpoints

### List Appliances
```bash
GET /devices/appliances/

Query Parameters:
- device: {device_id}
- room: {room_name}
- state: 0 or 1
- is_active: true or false

Response (200):
{
  "count": 8,
  "results": [...]
}
```

### Get Appliance
```bash
GET /devices/appliances/{appliance_id}/

Response (200):
{
  "id": "uuid",
  "name": "Main Light",
  "virtual_pin": "V0",
  "state": 1,
  "icon": "fa-lightbulb",
  "room": "Living Room",
  "device": "uuid",
  ...
}
```

### Toggle Appliance
```bash
POST /devices/appliances/{appliance_id}/toggle/

Response (200):
{
  "id": "uuid",
  "name": "Main Light",
  "state": 0,  // Toggled
  ...
}
```

### Set Appliance State
```bash
POST /devices/appliances/{appliance_id}/set_state/

Request:
{
  "state": 1
}

Response (200):
{
  "id": "uuid",
  "name": "Main Light",
  "state": 1,
  ...
}
```

### Get Appliance History
```bash
GET /devices/appliances/{appliance_id}/history/

Response (200):
[
  {
    "id": "uuid",
    "action": "turned_on",
    "previous_state": 0,
    "new_state": 1,
    "triggered_by": "user",
    "timestamp": "2024-06-07T10:30:00Z"
  }
]
```

## Notification Endpoints

### List Notifications
```bash
GET /notifications/

Query Parameters:
- is_read: true or false

Response (200):
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "title": "Device Offline",
      "message": "Living Room device went offline",
      "notification_type": "device_offline",
      "is_read": false,
      "created_at": "2024-06-07T10:30:00Z"
    }
  ]
}
```

### Get Unread Notifications
```bash
GET /notifications/unread/

Response (200):
[...]
```

### Mark Notification as Read
```bash
POST /notifications/{notification_id}/mark_as_read/

Response (200):
{
  "message": "Notification marked as read"
}
```

### Mark All as Read
```bash
POST /notifications/mark_all_as_read/

Response (200):
{
  "message": "All notifications marked as read"
}
```

### Get Notification Preferences
```bash
GET /notifications/preferences/

Response (200):
{
  "device_offline_in_app": true,
  "device_offline_email": true,
  "email_frequency": "immediate",
  ...
}
```

### Update Notification Preferences
```bash
PUT /notifications/preferences/

Request:
{
  "device_offline_in_app": true,
  "email_frequency": "daily"
}

Response (200):
{...updated preferences...}
```

## User Endpoints

### Get Current User
```bash
GET /accounts/users/me/

Response (200):
{
  "id": "uuid",
  "username": "username",
  "email": "user@example.com",
  "role": "user",
  "devices_count": 2,
  "api_keys_count": 3
}
```

### Update Profile
```bash
POST /accounts/users/me/update_profile/

Request:
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "IoT Enthusiast"
}

Response (200):
{...updated user...}
```

### Change Password
```bash
POST /accounts/users/me/change_password/

Request:
{
  "old_password": "current_password",
  "new_password": "new_password",
  "new_password_confirm": "new_password"
}

Response (200):
{
  "message": "Password changed successfully"
}
```

### Toggle Theme
```bash
POST /accounts/users/me/toggle_theme/

Response (200):
{
  "theme": "dark"
}
```

## API Key Endpoints

### List API Keys
```bash
GET /accounts/api-keys/

Response (200):
{
  "results": [
    {
      "id": "uuid",
      "name": "Device API Key",
      "key": "key_preview...",
      "is_active": true,
      "created_at": "2024-06-07T10:30:00Z"
    }
  ]
}
```

### Create API Key
```bash
POST /accounts/api-keys/

Request:
{
  "name": "Mobile App Key",
  "can_read_devices": true,
  "can_write_devices": true,
  "rate_limit": 1000
}

Response (201):
{
  "id": "uuid",
  "key": "full_api_key_displayed_once",
  "name": "Mobile App Key",
  ...
}
```

### Regenerate API Key
```bash
POST /accounts/api-keys/{key_id}/regenerate/

Response (200):
{
  "message": "API key regenerated",
  "key": "new_api_key"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "status": "error",
  "message": "Error description",
  "errors": {
    "field": ["Field error"]
  }
}
```

### Common Error Codes

- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Missing or invalid authentication
- **403**: Forbidden - Permission denied
- **404**: Not Found - Resource not found
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error

## Rate Limiting

All authenticated users have a rate limit of:
- 1000 requests per hour (user)
- 100 requests per hour (anonymous)

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1622794800
```

## WebSocket Endpoints

### Device Status WebSocket
```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws/devices/');

// Messages
ws.send(JSON.stringify({
  type: 'get_status'
}));

ws.onmessage = function(e) {
  const data = JSON.parse(e.data);
  console.log(data);
};
```

### Appliance Control WebSocket
```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws/appliances/');

// Toggle appliance
ws.send(JSON.stringify({
  type: 'toggle_appliance',
  appliance_id: 'appliance_uuid'
}));

// Set state
ws.send(JSON.stringify({
  type: 'set_appliance_state',
  appliance_id: 'appliance_uuid',
  state: 1
}));
```





http://localhost:8000/api/device/heartbeat/
{

"api_key": "Ua6mDMZ0GvT3lmwRMHrDp4tbWE32q9PwnF52RZuN",
"device_id": "Room1_001"
}

{
"status": "success",
"message": "Heartbeat received"
}

unfortuantenly my esp is not on, then how i am getting success