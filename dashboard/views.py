"""
Dashboard views for web interface.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from devices.models import Device, Appliance, ApplianceHistory, WaterPumpTimer, OTAUpdate
from notifications.models import Notification
from accounts.models import User


from django.http import JsonResponse

@login_required
def dashboard_view(request):
    """Main dashboard view."""
    user = request.user
    
    if user.role == 'admin':
        devices = Device.objects.all()
        users = User.objects.all()
    else:
        devices = Device.objects.filter(user=user)
        users = None
    
    context = {
        'devices': devices,
        'users': users,
        'total_devices': devices.count(),
        'online_devices': devices.filter(status='online').count(),
        'offline_devices': devices.filter(status='offline').count(),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def devices_view(request):
    """Devices list view."""
    user = request.user
    
    if user.role == 'admin':
        devices = Device.objects.all()
    else:
        devices = Device.objects.filter(user=user)
    
    context = {
        'devices': devices,
    }
    
    return render(request, 'dashboard/devices.html', context)


@login_required
def device_detail_view(request, device_id):
    """Device detail view."""
    user = request.user
    device = Device.objects.get(id=device_id)
    
    if device.user != user and user.role != 'admin':
        return render(request, '403.html', status=403)
    
    appliances = device.appliances.all()
    history = ApplianceHistory.objects.filter(appliance__device=device).order_by('-timestamp')[:50]
    shared_api_key = device.user.get_or_create_api_key()
    
    context = {
        'device': device,
        'appliances': appliances,
        'history': history,
        'shared_api_key': shared_api_key,
    }
    
    return render(request, 'dashboard/device_detail.html', context)


@login_required
def rooms_view(request):
    """Rooms view to organize appliances by room."""
    user = request.user
    
    if user.role == 'admin':
        appliances = Appliance.objects.all()
    else:
        appliances = Appliance.objects.filter(device__user=user)
    
    # Group by room, falling back to the device name when room is blank.
    rooms_info = {}
    for app in appliances:
        room = app.room.strip() if app.room and app.room.strip() else app.device.device_name or 'Uncategorized'
        if room not in rooms_info:
            rooms_info[room] = {
                'appliances': [],
                'devices': set(),
            }
        rooms_info[room]['appliances'].append(app)
        if app.device:
            rooms_info[room]['devices'].add(app.device)

    # Convert sets to lists and compute room-level online status
    for r, info in list(rooms_info.items()):
        devices_list = list(info['devices'])
        info['devices'] = devices_list
        info['is_online'] = any([d.is_online() for d in devices_list]) if devices_list else False
        # compute last_seen for the room as the most recent last_heartbeat or last_seen among devices
        latest = None
        for d in devices_list:
            cand = d.last_heartbeat or d.last_seen
            if cand:
                if latest is None or cand > latest:
                    latest = cand
        info['last_seen'] = latest

    context = {
        'rooms_info': rooms_info,
    }
    
    return render(request, 'dashboard/rooms.html', context)


@login_required
def activity_logs_view(request):
    """Activity logs view."""
    user = request.user
    
    if user.role == 'admin':
        logs = ApplianceHistory.objects.all().order_by('-timestamp')[:200]
    else:
        devices = Device.objects.filter(user=user)
        logs = ApplianceHistory.objects.filter(
            appliance__device__in=devices
        ).order_by('-timestamp')[:200]
    
    context = {
        'logs': logs,
    }
    
    return render(request, 'dashboard/activity_logs.html', context)


@login_required
def notifications_view(request):
    """Notifications view."""
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:50]
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'dashboard/notifications.html', context)


@login_required
def profile_view(request):
    """User profile view."""
    user = request.user
    shared_api_key = user.get_or_create_api_key()
    api_keys = user.api_keys.all()
    
    context = {
        'user': user,
        'api_keys': api_keys,
        'shared_api_key': shared_api_key,
    }
    
    return render(request, 'dashboard/profile.html', context)


@login_required
def settings_view(request):
    """Settings view."""
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'dashboard/settings.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics."""
    user = request.user
    
    if user.role == 'admin':
        total_users = User.objects.count()
        total_devices = Device.objects.count()
        online_devices = Device.objects.filter(status='online').count()
        offline_devices = Device.objects.filter(status='offline').count()
        total_appliances = Appliance.objects.count()
    else:
        total_users = 1
        total_devices = Device.objects.filter(user=user).count()
        online_devices = Device.objects.filter(user=user, status='online').count()
        offline_devices = Device.objects.filter(user=user, status='offline').count()
        total_appliances = Appliance.objects.filter(device__user=user).count()
    
    return Response({
        'total_users': total_users,
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'total_appliances': total_appliances,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """Get dashboard data for rendering."""
    user = request.user
    
    if user.role == 'admin':
        devices = Device.objects.all()
        appliances = Appliance.objects.all()
    else:
        devices = Device.objects.filter(user=user)
        appliances = Appliance.objects.filter(device__user=user)
    
    # Group appliances by room, falling back to the device name when room is blank.
    rooms = {}
    for app in appliances:
        room = app.room.strip() if app.room and app.room.strip() else app.device.device_name or 'Uncategorized'
        if room not in rooms:
            rooms[room] = []
        rooms[room].append({
            'id': str(app.id),
            'name': app.name,
            'state': app.state,
            'value': app.value,
            'appliance_type': app.appliance_type,
            'icon': app.icon,
            'virtual_pin': app.virtual_pin,
            'device_name': app.device.device_name,
            'last_updated': app.last_updated.isoformat(),
        })
    
    return Response({
        'devices': [
            {
                'id': str(d.id),
                'name': d.device_name,
                'status': d.status,
                'online': d.is_online(),
                'wifi_signal': d.wifi_signal,
            } for d in devices
        ],
        'rooms': rooms,
    })

@login_required
def water_monitoring_view(request):
    """Water monitoring dashboard."""
    user = request.user
    if user.role == 'admin':
        devices = Device.objects.filter(device_role='water_monitor').order_by('-last_seen')
    else:
        devices = Device.objects.filter(user=user, device_role='water_monitor').order_by('-last_seen')

    context = {
        'devices': devices,
    }
    return render(request, 'dashboard/water_monitoring.html', context)

@login_required
def ota_update_view(request):
    """OTA firmware update dashboard."""
    user = request.user
    is_admin_user = (user.role == 'admin') or user.is_staff or user.is_superuser
    if is_admin_user:
        devices = Device.objects.all()
    else:
        devices = Device.objects.filter(user=user)
    # Prepare OTA updates for server-side rendering so the page shows updates
    if is_admin_user:
        updates_qs = OTAUpdate.objects.all().order_by('-created_at')[:50]
    else:
        updates_qs = OTAUpdate.objects.filter(device__user=user).order_by('-created_at')[:50]
        if not updates_qs:
            updates_qs = OTAUpdate.objects.all().order_by('-created_at')[:50]

    updates = []
    for u in updates_qs:
        updates.append({
            'id': str(u.id),
            'version': u.version,
            'device_name': u.device.device_name,
            'status': u.status,
            'file_size': u.file_size,
            'created_at': u.created_at,
            'download_progress': u.download_progress,
        })

    context = {
        'devices': devices,
        'updates': updates,
    }
    return render(request, 'dashboard/ota_update.html', context)

@login_required
def ota_updates_api(request):
    """Get list of OTA updates for the user."""
    user = request.user
    is_admin_user = (user.role == 'admin') or user.is_staff or user.is_superuser
    if is_admin_user:
        updates = OTAUpdate.objects.all().order_by('-created_at')[:50]
    else:
        updates = OTAUpdate.objects.filter(device__user=user).order_by('-created_at')[:50]
        # If the user has no device-specific updates, show recent global updates as a
        # fallback so the dashboard isn't empty (useful for demo/dev environments).
        if not updates:
            updates = OTAUpdate.objects.all().order_by('-created_at')[:50]
        
    data = []
    for update in updates:
        data.append({
            'id': str(update.id),
            'version': update.version,
            'device_name': update.device.device_name,
            'status': update.status,
            'file_size': update.file_size,
            'created_at': update.created_at.isoformat(),
            'download_progress': update.download_progress,
        })
    return JsonResponse({'updates': data})

@login_required
def ota_download_api(request, update_id):
    """Get download URL for a specific OTA update."""
    user = request.user
    try:
        update = OTAUpdate.objects.get(id=update_id)
        # Verify user has permission to download
        if user.role != 'admin' and update.device.user != user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if update.bin_file:
            download_url = update.bin_file.url
            return JsonResponse({'download_url': download_url})
        else:
            return JsonResponse({'error': 'Firmware file not found'}, status=404)
    except OTAUpdate.DoesNotExist:
        return JsonResponse({'error': 'Update not found'}, status=404)

import json
from django.views.decorators.http import require_POST
from django.utils.timezone import now

def get_pump_appliance(device):
    """Get pump appliance for a device with fallback logic."""
    # Try to find by appliance_type first
    pump = Appliance.objects.filter(device=device, appliance_type='pump').first()
    if pump:
        return pump
    
    # Fallback: try to find by name containing 'pump' (case-insensitive)
    pump = Appliance.objects.filter(device=device, name__icontains='pump').first()
    if pump:
        return pump
    
    # Fallback: get first appliance of any type if only one exists
    appliances = Appliance.objects.filter(device=device)
    if appliances.count() == 1:
        return appliances.first()
    
    return None

@login_required
def pump_status_api(request):
    """Get pump and timer status for a water monitoring device."""
    try:
        device_id = request.GET.get('device_id')
        user = request.user
        if user.role == 'admin':
            device = Device.objects.get(id=device_id)
        else:
            device = Device.objects.get(id=device_id, user=user)

        pump = get_pump_appliance(device)
        timer = None
        try:
            timer = WaterPumpTimer.objects.get(device=device)
        except WaterPumpTimer.DoesNotExist:
            timer = None

        return JsonResponse({
            'status': 'success',
            'pump_state': pump.state if pump else 0,
            'pump_status': 'ON' if pump and pump.state == 1 else 'OFF',
            'pump_exists': pump is not None,
            'timer': {
                'hours': timer.hours if timer else 0,
                'minutes': timer.minutes if timer else 0,
                'seconds': timer.seconds if timer else 0,
                'is_active': timer.is_active if timer else False,
                'is_running': timer.is_running if timer else False,
                'remaining_seconds': timer.remaining_seconds if timer else 0
            }
        })
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Device not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def toggle_pump_api(request):
    """Toggle water pump for a device via dashboard."""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        state = int(data.get('state', 0))
        
        user = request.user
        if user.role == 'admin':
            device = Device.objects.get(id=device_id)
        else:
            device = Device.objects.get(id=device_id, user=user)
            
        # Find the pump appliance with fallback logic
        pump = get_pump_appliance(device)
        if not pump:
            return JsonResponse({'status': 'error', 'message': 'No pump appliance configured for this device'})
            
        old_state = pump.state
        pump.state = state
        if pump.value is None:
            pump.value = state
        pump.save(update_fields=['state', 'value'])
        pump.refresh_from_db()  # Refresh to get updated state
        
        action = 'turned_on' if state == 1 else 'turned_off'
        ApplianceHistory.objects.create(
            appliance=pump,
            previous_state=old_state,
            new_state=pump.state,
            action=action,
            triggered_by='user',
            triggered_by_user=user
        )

        timer_deactivated = False
        try:
            timer = WaterPumpTimer.objects.get(device=device)
            if timer.is_active or timer.is_running:
                timer.is_active = False
                timer.is_running = False
                timer.started_at = None
                timer.save(update_fields=['is_active', 'is_running', 'started_at'])
                timer_deactivated = True
        except WaterPumpTimer.DoesNotExist:
            pass
        
        return JsonResponse({
            'status': 'success',
            'message': f'Pump turned {"ON" if state == 1 else "OFF"}',
            'state': pump.state,
            'timer_deactivated': timer_deactivated,
            'debug': {'pump_name': pump.name, 'pump_type': pump.appliance_type, 'saved_state': pump.state}
        })
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Device not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@require_POST
def start_timer_api(request):
    """Start timer for a device via dashboard."""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        user = request.user
        if user.role == 'admin':
            device = Device.objects.get(id=device_id)
        else:
            device = Device.objects.get(id=device_id, user=user)
            
        pump = Appliance.objects.filter(device=device, appliance_type='pump').first()
        if pump and pump.state == 1:
            return JsonResponse({'status': 'error', 'message': 'Cannot start timer while pump is ON. Turn pump OFF first.'})

        timer = WaterPumpTimer.objects.get(device=device)
        timer.is_running = True
        timer.started_at = now()
        timer.save(update_fields=['is_running', 'started_at'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Timer started',
            'total_seconds': timer.total_seconds,
            'remaining_seconds': timer.remaining_seconds
        })
    except WaterPumpTimer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Timer not configured'})
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Device not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def stop_timer_api(request):
    """Stop an active timer for a device via dashboard."""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')

        user = request.user
        if user.role == 'admin':
            device = Device.objects.get(id=device_id)
        else:
            device = Device.objects.get(id=device_id, user=user)

        timer = WaterPumpTimer.objects.get(device=device)
        timer.is_running = False
        timer.started_at = None
        timer.save(update_fields=['is_running', 'started_at'])

        return JsonResponse({
            'status': 'success',
            'message': 'Timer stopped',
            'is_running': False,
            'total_seconds': timer.total_seconds,
            'remaining_seconds': 0,
            'timer': {
                'hours': timer.hours,
                'minutes': timer.minutes,
                'seconds': timer.seconds,
                'is_active': timer.is_active,
                'is_running': False,
                'remaining_seconds': 0
            }
        })
    except WaterPumpTimer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Timer not configured'})
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Device not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
