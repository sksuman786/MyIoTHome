"""
REST API views for ESP8266/ESP32 devices.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.utils.timezone import now

from devices.models import Device, Appliance, ApplianceHistory, DeviceData, WaterMonitoringData, WaterPumpTimer, OTAUpdate
from accounts.models import APIKey
from accounts.authentication import APIKeyAuthentication
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.utils import send_device_status_notification
from django.shortcuts import get_object_or_404


def get_device_by_user_api_key(api_key, device_id=None):
    """Locate a device with the shared user API key and optional device_id."""
    try:
        api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
    except APIKey.DoesNotExist:
        return None

    devices = Device.objects.filter(user=api_key_obj.user, is_active=True)
    if device_id:
        return devices.filter(device_id=device_id).first()
    if devices.count() == 1:
        return devices.first()
    return None


@api_view(['POST'])
@permission_classes([AllowAny])
def device_auth(request):
    """
    Device authentication endpoint.
    
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
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    
    if not api_key or not device_id:
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        if not device.is_active:
            return Response({
                'status': 'error',
                'message': 'Device is inactive'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last seen
        device.last_seen = now()
        device.status = 'online'
        device.save(update_fields=['last_seen', 'status'])
        try:
            send_device_status_notification(device.user, device, device.status)
        except Exception:
            pass

        # Broadcast status update to any connected dashboards via channels
        try:
            channel_layer = get_channel_layer()
            group_name = f"devices_user_{device.user.id}_devices"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'device_status_update',
                    'data': {
                        'type': 'device_update',
                        'id': str(device.id),
                        'device_id': device.device_id,
                        'device_name': device.device_name,
                        'status': device.status,
                        'online': device.is_online(),
                        'wifi_signal': device.wifi_signal,
                        'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                    }
                }
            )
        except Exception:
            pass
        
        return Response({
            'status': 'success',
            'message': 'Device authenticated successfully',
            'device_id': device.device_id,
            'device_name': device.device_name
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid device_id or api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_appliance_states(request):
    """
    Get current state of all appliances.
    
    GET /api/device/states/?api_key=YOUR_API_KEY
    
    Response:
    {
        "status": "success",
        "V0": 1,
        "V1": 0,
        "V2": 1,
        "V3": 0,
        ...
    }
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')
    
    if not api_key:
        return Response({
            'status': 'error',
            'message': 'api_key is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            return Response({
                'status': 'error',
                'message': 'Invalid api_key or device_id'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        appliances = device.appliances.filter(is_active=True)
        states = {'status': 'success'}
        
        # for appliance in appliances:
        #     states[appliance.virtual_pin] = appliance.value if appliance.value is not None else appliance.state

        for appliance in appliances:
            if appliance.appliance_type == 'slider':
                states[appliance.virtual_pin] = appliance.value or 0

            elif appliance.appliance_type == 'display':
                states[appliance.virtual_pin] = appliance.value or 0

            else:
                states[appliance.virtual_pin] = appliance.state
        
        return Response(states)
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_device_status(request):
    """
    Update device status with sensor data.
    
    POST /api/device/status/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001",
        "temperature": 28.5,
        "humidity": 65,
        "wifi_signal": -55,
        "uptime": 3600,
        "free_memory": 15000,
        "power_consumption": 2.5
    }
    
    Response:
    {
        "status": "success",
        "message": "Status updated",
        "device_id": "ESP8266_001"
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    
    if not api_key or not device_id:
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        
        # Update device network/metric data
        device.wifi_signal = request.data.get('wifi_signal', device.wifi_signal)
        device.ip_address = request.data.get('ip_address', device.ip_address)
        device.last_seen = now()
        device.status = 'online'
        device.save()
        try:
            send_device_status_notification(device.user, device, device.status)
        except Exception:
            pass
        
        # Log device data (environmental fields removed)
        DeviceData.objects.create(
            device=device,
            wifi_signal=request.data.get('wifi_signal'),
            wifi_quality=request.data.get('wifi_quality'),
            uptime=request.data.get('uptime'),
            free_memory=request.data.get('free_memory'),
            power_consumption=request.data.get('power_consumption')
        )
        
        return Response({
            'status': 'success',
            'message': 'Status updated successfully',
            'device_id': device.device_id
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid device_id or api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def device_heartbeat(request):
    """
    Record device heartbeat to track online status.
    
    POST /api/device/heartbeat/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001"
    }
    
    Response:
    {
        "status": "success",
        "message": "Heartbeat received"
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    
    if not api_key or not device_id:
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        device.last_heartbeat = now()
        device.status = 'online'
        device.save(update_fields=['last_heartbeat', 'status'])
        try:
            send_device_status_notification(device.user, device, device.status)
        except Exception:
            pass

        # Broadcast status update to dashboards for this user
        try:
            channel_layer = get_channel_layer()
            group_name = f"devices_user_{device.user.id}_devices"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'device_status_update',
                    'data': {
                        'type': 'device_update',
                        'id': str(device.id),
                        'device_id': device.device_id,
                        'device_name': device.device_name,
                        'status': device.status,
                        'online': device.is_online(),
                        'wifi_signal': device.wifi_signal,
                        'last_heartbeat': device.last_heartbeat.isoformat() if device.last_heartbeat else None,
                    }
                }
            )
        except Exception:
            pass
        
        return Response({
            'status': 'success',
            'message': 'Heartbeat received'
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid device_id or api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    """
    External API to get device online/offline status for a user.

    GET /api/system/status/?api_key=YOUR_API_KEY[&device_id=DEVICE_ID]
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')

    if not api_key:
        return Response({'status': 'error', 'message': 'api_key is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
    except APIKey.DoesNotExist:
        return Response({'status': 'error', 'message': 'Invalid api_key'}, status=status.HTTP_401_UNAUTHORIZED)

    devices_qs = Device.objects.filter(user=api_key_obj.user, is_active=True)
    if device_id:
        devices_qs = devices_qs.filter(device_id=device_id)

    devices = []
    for d in devices_qs:
        devices.append({
            'id': str(d.id),
            'device_id': d.device_id,
            'device_name': d.device_name,
            'device_role': d.device_role,
            'status': d.status,
            'is_online': d.is_online(),
            'last_heartbeat': d.last_heartbeat.isoformat() if d.last_heartbeat else None,
            'last_seen': d.last_seen.isoformat() if d.last_seen else None,
            'wifi_signal': d.wifi_signal,
            'heartbeat_timeout_seconds': d.heartbeat_timeout_seconds,
        })

    return Response({'status': 'success', 'devices': devices})


@api_view(['POST'])
@permission_classes([AllowAny])
def update_appliance_state(request):
    """
    Update appliance state from device.
    
    POST /api/device/appliance/state/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001",
        "virtual_pin": "V0",
        "state": 1
    }
    
    Response:
    {
        "status": "success",
        "message": "Appliance state updated",
        "virtual_pin": "V0",
        "state": 1
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    virtual_pin = request.data.get('virtual_pin')
    state = request.data.get('state')
    value = request.data.get('value')
    
    if api_key is None or device_id is None or virtual_pin is None or (state is None and value is None):
        return Response({
            'status': 'error',
            'message': 'api_key, device_id, virtual_pin, and state or value are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        appliance = Appliance.objects.get(device=device, virtual_pin=virtual_pin)
        
        old_state = appliance.state
        if value is not None:
            new_value = int(value)
            appliance.value = new_value
            appliance.state = 1 if new_value > 0 else 0
            action = 'turned_on' if new_value > 0 else 'turned_off'
        else:
            new_state = int(state)
            # appliance.state = new_state
            # if appliance.value is None:
            #     appliance.value = new_state
            # action = 'turned_on' if new_state == 1 else 'turned_off'
       
            new_state = int(state)

            if appliance.appliance_type == 'slider':
                appliance.value = new_state
                appliance.state = 1 if new_state > 0 else 0
                action = 'updated'

            elif appliance.appliance_type == 'display':
                appliance.value = new_state
                action = 'updated'

            else:
                appliance.state = new_state

                if appliance.value is None:
                    appliance.value = new_state

                action = 'turned_on' if new_state == 1 else 'turned_off'    
        appliance.save()
        
        # Record history
        ApplianceHistory.objects.create(
            appliance=appliance,
            previous_state=old_state,
            new_state=appliance.state,
            action=action,
            triggered_by='device'
        )
        
        return Response({
            'status': 'success',
            'message': 'Appliance state updated',
            'virtual_pin': virtual_pin,
            'state': appliance.state,
            'value': appliance.value
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid device_id or api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Appliance.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'Appliance with virtual_pin {virtual_pin} not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def set_appliance_state(request):
    """
    Request to set appliance state (called by user).
    
    POST /api/device/appliance/set/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001",
        "virtual_pin": "V0",
        "state": 1
    }
    
    Response:
    {
        "status": "success",
        "message": "Request sent to device",
        "virtual_pin": "V0",
        "state": 1
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    virtual_pin = request.data.get('virtual_pin')
    state = request.data.get('state')
    value = request.data.get('value')
    
    if api_key is None or device_id is None or virtual_pin is None or (state is None and value is None):
        return Response({
            'status': 'error',
            'message': 'api_key, device_id, virtual_pin, and state or value are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        appliance = Appliance.objects.get(device=device, virtual_pin=virtual_pin)
        
        if not appliance.can_control:
            return Response({
                'status': 'error',
                'message': 'This appliance cannot be controlled'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update state or numeric value
        old_state = appliance.state
        if value is not None:
            new_value = int(value)
            appliance.value = new_value
            appliance.state = 1 if new_value > 0 else 0
            action = 'turned_on' if new_value > 0 else 'turned_off'
        else:
            new_state = int(state)
            appliance.state = new_state
            if appliance.value is None:
                appliance.value = new_state
            action = 'turned_on' if new_state == 1 else 'turned_off'
        appliance.save()
        
        # Record history
        ApplianceHistory.objects.create(
            appliance=appliance,
            previous_state=old_state,
            new_state=appliance.state,
            action=action,
            triggered_by='user'
        )
        
        return Response({
            'status': 'success',
            'message': 'Appliance state set successfully',
            'virtual_pin': virtual_pin,
            'state': appliance.state,
            'value': appliance.value
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid device_id or api_key'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Appliance.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f'Appliance with virtual_pin {virtual_pin} not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_documentation(request):
    """Get API documentation."""
    return Response({
        'title': 'MyHome IoT API Documentation',
        'version': '1.0.0',
        'endpoints': {
            'device_auth': '/api/device/auth/',
            'get_states': '/api/device/states/',
            'update_status': '/api/device/status/',
            'heartbeat': '/api/device/heartbeat/',
            'update_appliance_state': '/api/device/appliance/state/',
            'set_appliance_state': '/api/device/appliance/set/',
            'documentation': '/api/docs/'
        }
    })


# Water Monitoring API Endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def save_water_monitoring_data(request):
    """
    Save water quality monitoring data from device.
    
    POST /api/device/water/data/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001",
        "water_percentage": 75.5,
        "tds": 450,
        "ph": 7.2,
        "temperature": 28.5
    }
    
    Response:
    {
        "status": "success",
        "message": "Water data saved successfully",
        "data": {...}
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    water_percentage = request.data.get('water_percentage')
    tds = request.data.get('tds')
    ph = request.data.get('ph')
    temperature = request.data.get('temperature')
    
    if not all([api_key, device_id, water_percentage is not None, tds is not None, ph is not None, temperature is not None]):
        return Response({
            'status': 'error',
            'message': 'api_key, device_id, water_percentage, tds, ph, and temperature are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            api_key_obj = APIKey.objects.filter(key=api_key, is_active=True).first()
            if not api_key_obj:
                raise Device.DoesNotExist
            # Auto-register a dedicated water monitoring device if it does not exist yet.
            device = Device.objects.create(
                user=api_key_obj.user,
                device_id=device_id,
                device_name=device_id,
                device_type='esp8266',
                device_role='water_monitor',
                status='online',
                is_active=True,
            )
        
        device.last_seen = now()
        device.save(update_fields=['last_seen', 'status'])
        
        water_data = WaterMonitoringData.objects.create(
            device=device,
            water_percentage=float(water_percentage),
            tds=float(tds),
            ph=float(ph),
            temperature=float(temperature)
        )
        
        return Response({
            'status': 'success',
            'message': 'Water data saved successfully',
            'data': {
                'id': str(water_data.id),
                'water_percentage': water_data.water_percentage,
                'tds': water_data.tds,
                'ph': water_data.ph,
                'temperature': water_data.temperature,
                'timestamp': water_data.timestamp.isoformat()
            }
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid api_key or device_id'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_water_monitoring_data(request):
    """
    Get latest water quality monitoring data.
    
    GET /api/device/water/data/?api_key=YOUR_KEY&device_id=ESP_ID&limit=10
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')
    limit = int(request.query_params.get('limit', 50))

    if api_key:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            return Response({
                'status': 'error',
                'message': 'Invalid api_key or device_id'
            }, status=status.HTTP_401_UNAUTHORIZED)
    elif request.user.is_authenticated:
        if not device_id:
            return Response({
                'status': 'error',
                'message': 'device_id is required for authenticated requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            device = Device.objects.get(id=device_id, user=request.user)
        except Device.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid device_id'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'status': 'error',
            'message': 'api_key or authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)

    water_data = WaterMonitoringData.objects.filter(device=device).order_by('-timestamp')[:limit]
    data = [{
        'id': str(d.id),
        'water_percentage': d.water_percentage,
        'tds': d.tds,
        'ph': d.ph,
        'temperature': d.temperature,
        'timestamp': d.timestamp.isoformat()
    } for d in water_data]
    
    return Response({
        'status': 'success',
        'data': data
    })


# Water Pump Timer API Endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pump_timer(request):
    """
    Create or update water pump timer.
    
    POST /api/water/pump/timer/
    
    {
        "device_id": "device_uuid",
        "hours": 0,
        "minutes": 30,
        "seconds": 0,
        "is_active": true
    }
    """
    device_id = request.data.get('device_id')
    hours = request.data.get('hours', 0)
    minutes = request.data.get('minutes', 0)
    seconds = request.data.get('seconds', 0)
    is_active = request.data.get('is_active', False)
    
    try:
        device = Device.objects.get(id=device_id, user=request.user)
        timer, created = WaterPumpTimer.objects.get_or_create(device=device)
        if timer.is_running:
            return Response({
                'status': 'error',
                'message': 'Cannot create or update timer while an active timer is running'
            }, status=status.HTTP_400_BAD_REQUEST)

        timer.hours = hours
        timer.minutes = minutes
        timer.seconds = seconds
        timer.is_active = is_active
        timer.save()
        
        return Response({
            'status': 'success',
            'message': 'Timer saved successfully',
            'timer': {
                'id': str(timer.id),
                'hours': timer.hours,
                'minutes': timer.minutes,
                'seconds': timer.seconds,
                'total_seconds': timer.total_seconds,
                'is_active': timer.is_active,
                'is_running': timer.is_running
            }
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pump_timer(request):
    """Get water pump timer status."""
    device_id = request.query_params.get('device_id')
    
    try:
        device = Device.objects.get(id=device_id, user=request.user)
        timer = WaterPumpTimer.objects.get(device=device)
        
        return Response({
            'status': 'success',
            'timer': {
                'id': str(timer.id),
                'hours': timer.hours,
                'minutes': timer.minutes,
                'seconds': timer.seconds,
                'total_seconds': timer.total_seconds,
                'remaining_seconds': timer.remaining_seconds,
                'is_active': timer.is_active,
                'is_running': timer.is_running,
                'started_at': timer.started_at.isoformat() if timer.started_at else None
            }
        })
    except (Device.DoesNotExist, WaterPumpTimer.DoesNotExist):
        return Response({
            'status': 'error',
            'message': 'Timer or device not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def start_pump_timer(request):
    """
    Start water pump timer (called by device).
    
    POST /api/device/water/pump/start/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001"
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    
    if not api_key or not device_id:
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        
        timer = WaterPumpTimer.objects.get(device=device)
        timer.is_running = True
        timer.started_at = now()
        timer.save()
        
        return Response({
            'status': 'success',
            'message': 'Timer started',
            'timer': {
                'hours': timer.hours,
                'minutes': timer.minutes,
                'seconds': timer.seconds,
                'total_seconds': timer.total_seconds,
                'remaining_seconds': timer.remaining_seconds
            }
        })
    except WaterPumpTimer.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Timer not configured'
        }, status=status.HTTP_404_NOT_FOUND)
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid api_key or device_id'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_device_pump_timer(request):
    """
    Get current water pump timer status for a device.

    GET /api/device/water/pump/timer/status/?api_key=YOUR_KEY&device_id=ESP_ID
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')

    if not api_key:
        return Response({
            'status': 'error',
            'message': 'api_key is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    device = get_device_by_user_api_key(api_key, device_id)
    if not device:
        return Response({
            'status': 'error',
            'message': 'Invalid api_key or device_id'
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        timer = WaterPumpTimer.objects.get(device=device)
        return Response({
            'status': 'success',
            'timer': {
                'id': str(timer.id),
                'hours': timer.hours,
                'minutes': timer.minutes,
                'seconds': timer.seconds,
                'total_seconds': timer.total_seconds,
                'remaining_seconds': timer.remaining_seconds,
                'is_active': timer.is_active,
                'is_running': timer.is_running,
                'started_at': timer.started_at.isoformat() if timer.started_at else None
            }
        })
    except WaterPumpTimer.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Timer not configured'
        }, status=status.HTTP_404_NOT_FOUND)


# OTA Update API Endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_ota_update(request):
    """
    Upload new OTA firmware file.
    
    POST /api/ota/upload/
    
    Multipart form data:
    - device_id: Target device UUID (required)
    - version: Version string e.g. "v1.2.3" (required)
    - bin_file: Binary file (required)
    - notes: Optional release notes
    """
    device_id = request.data.get('device_id')
    version = request.data.get('version')
    bin_file = request.FILES.get('bin_file')
    notes = request.data.get('notes', '')
    
    if not all([device_id, version, bin_file]):
        return Response({
            'status': 'error',
            'message': 'device_id, version, and bin_file are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = Device.objects.get(id=device_id, user=request.user)
        
        # Calculate file checksum
        import hashlib
        checksum = hashlib.sha256(bin_file.read()).hexdigest()
        bin_file.seek(0)  # Reset file pointer
        
        ota_update = OTAUpdate.objects.create(
            device=device,
            bin_file=bin_file,
            file_size=bin_file.size,
            checksum=checksum,
            version=version,
            notes=notes
        )
        
        return Response({
            'status': 'success',
            'message': 'OTA update uploaded successfully',
            'update': {
                'id': str(ota_update.id),
                'version': ota_update.version,
                'file_size': ota_update.file_size,
                'checksum': ota_update.checksum,
                'status': ota_update.status
            }
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def ota_check_version(request):
    """
    Check for latest firmware version for a specific device.
    
    GET /api/ota/check/?api_key=USER_API_KEY&device_id=WaterMonitor_001&current_version=v1.0.0
    
    Response if update available:
    {
        "status": "success",
        "update_available": true,
        "latest_version": "v1.2.3",
        "download_url": "https://.../media/ota_updates/firmware.bin",
        "file_size": 1234567,
        "checksum": "sha256hash",
        "update_id": "uuid"
    }
    
    Response if no update:
    {
        "status": "success",
        "update_available": false,
        "message": "You are running the latest version"
    }
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')
    current_version = request.query_params.get('current_version', '0.0.0')
    
    if not all([api_key, device_id]):
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get user from API key
        api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
        user = api_key_obj.user
        
        # Get the device (by hardware device_id string, e.g. WaterMonitor_001)
        device = Device.objects.get(device_id=device_id, user=user)
        
        # Get latest OTA update for THIS specific device
        latest_ota = OTAUpdate.objects.filter(
            device=device,
            status='pending'
        ).order_by('-created_at').first()
        
        if not latest_ota:
            return Response({
                'status': 'success',
                'update_available': False,
                'message': 'No updates available'
            })
        
        # Compare versions (simple string comparison; ideally use semver)
        if latest_ota.version > current_version:
            file_url = request.build_absolute_uri(latest_ota.bin_file.url)
            return Response({
                'status': 'success',
                'update_available': True,
                'latest_version': latest_ota.version,
                'download_url': file_url,
                'file_size': latest_ota.file_size,
                'checksum': latest_ota.checksum,
                'update_id': str(latest_ota.id)
            })
        else:
            return Response({
                'status': 'success',
                'update_available': False,
                'message': 'You are running the latest version'
            })
    
    except APIKey.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid API key'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found for your account'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_ota_update_download(request):
    """
    Download OTA firmware file (for ESP device).
    
    GET /api/device/ota/download/?api_key=KEY&device_id=ID
    
    Returns: Binary file stream
    """
    api_key = request.query_params.get('api_key')
    device_id = request.query_params.get('device_id')
    
    if not api_key or not device_id:
        return Response({
            'status': 'error',
            'message': 'api_key and device_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        
        # Get latest pending OTA update
        ota_update = OTAUpdate.objects.filter(
            device=device,
            status__in=['pending', 'downloading']
        ).order_by('-created_at').first()
        
        if not ota_update:
            return Response({
                'status': 'error',
                'message': 'No pending OTA updates'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update status to downloading
        ota_update.status = 'downloading'
        ota_update.started_at = now()
        ota_update.save()
        
        # Return file info
        return Response({
            'status': 'success',
            'update': {
                'id': str(ota_update.id),
                'version': ota_update.version,
                'file_size': ota_update.file_size,
                'checksum': ota_update.checksum,
                'download_url': request.build_absolute_uri(ota_update.bin_file.url)
            }
        })
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Invalid api_key or device_id'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_ota_progress(request):
    """
    Update OTA download progress.
    
    POST /api/device/ota/progress/
    
    {
        "api_key": "your_api_key_here",
        "device_id": "ESP8266_001",
        "update_id": "update_uuid",
        "progress": 45,
        "status": "downloading"
    }
    """
    api_key = request.data.get('api_key')
    device_id = request.data.get('device_id')
    update_id = request.data.get('update_id')
    progress = request.data.get('progress', 0)
    status_param = request.data.get('status', 'downloading')
    
    if not all([api_key, device_id, update_id]):
        return Response({
            'status': 'error',
            'message': 'api_key, device_id, and update_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        device = get_device_by_user_api_key(api_key, device_id)
        if not device:
            raise Device.DoesNotExist
        
        ota_update = OTAUpdate.objects.get(id=update_id, device=device)
        ota_update.download_progress = int(progress)
        
        if status_param == 'completed':
            ota_update.status = 'completed'
            ota_update.completed_at = now()
        
        ota_update.save()
        
        return Response({
            'status': 'success',
            'message': 'Progress updated',
            'progress': ota_update.download_progress
        })
    except (Device.DoesNotExist, OTAUpdate.DoesNotExist):
        return Response({
            'status': 'error',
            'message': 'Invalid api_key, device_id, or update_id'
        }, status=status.HTTP_401_UNAUTHORIZED)

