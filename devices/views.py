"""
Views for device and appliance management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from devices.models import Device, Appliance, ApplianceHistory, DeviceData, DeviceFirmware
from devices.serializers import (
    DeviceSerializer, DeviceDetailSerializer, DeviceCreateUpdateSerializer,
    ApplianceSerializer, ApplianceHistorySerializer, DeviceDataSerializer,
    DeviceFirmwareSerializer, ApplianceToggleSerializer
)
from notifications.utils import send_device_status_notification


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for device management."""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'device_type', 'device_role', 'is_active']
    search_fields = ['device_name', 'device_id', 'mac_address', 'device_role']
    ordering_fields = ['created_at', 'last_seen']
    ordering = ['-last_seen']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Device.objects.all()
        return Device.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DeviceDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DeviceCreateUpdateSerializer
        return DeviceSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new device."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            DeviceDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_devices(self, request):
        """Get all devices for current user."""
        devices = self.get_queryset()
        serializer = self.get_serializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def state(self, request, pk=None):
        """Get current state of all appliances on a device."""
        device = self.get_object()
        appliances = device.appliances.filter(is_active=True)
        
        states = {
            app.virtual_pin: app.state for app in appliances
        }
        
        return Response({
            'device_id': device.device_id,
            'device_name': device.device_name,
            'status': device.status,
            'appliances': states
        })
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update device status with sensor data."""
        device = self.get_object()
        
        # Update network/metric data (environmental fields removed)
        device.wifi_signal = request.data.get('wifi_signal', device.wifi_signal)
        device.ip_address = request.data.get('ip_address', device.ip_address)
        device.save()
        
        # Create data log (no environmental fields)
        DeviceData.objects.create(
            device=device,
            wifi_signal=request.data.get('wifi_signal'),
            uptime=request.data.get('uptime'),
            free_memory=request.data.get('free_memory'),
            power_consumption=request.data.get('power_consumption')
        )
        
        return Response({
            'message': 'Device status updated',
            'device': DeviceDetailSerializer(device).data
        })
    
    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        """Record device heartbeat."""
        from django.utils.timezone import now
        import traceback

        device = self.get_object()
        device.last_heartbeat = now()
        device.status = 'online'
        device.save(update_fields=['last_heartbeat', 'status'])
        try:
            print("CALLING FCM...")
            send_device_status_notification(device.user, device, device.status)
            print("FCM COMPLETED")
        except Exception as e:
            print("FCM ERROR:", e)
            traceback.print_exc()
        return Response({'message': 'Heartbeat recorded'})
    
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get device activity history."""
        device = self.get_object()
        appliances = device.appliances.all()
        
        history = ApplianceHistory.objects.filter(
            appliance__in=appliances
        ).order_by('-timestamp')[:100]
        
        serializer = ApplianceHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def data_logs(self, request, pk=None):
        """Get device data logs."""
        device = self.get_object()
        data_logs = DeviceData.objects.filter(device=device).order_by('-timestamp')[:100]
        serializer = DeviceDataSerializer(data_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_api_key(self, request, pk=None):
        """Reset device API key."""
        return Response({'message': 'Per-device API keys removed; use account API keys instead.'}, status=status.HTTP_400_BAD_REQUEST)


class ApplianceViewSet(viewsets.ModelViewSet):
    """ViewSet for appliance management."""
    permission_classes = [IsAuthenticated]
    serializer_class = ApplianceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device', 'appliance_type', 'state', 'room', 'is_active']
    search_fields = ['name', 'virtual_pin', 'room']
    ordering_fields = ['created_at', 'name']
    ordering = ['room', 'name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Appliance.objects.all()
        return Appliance.objects.filter(device__user=user)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle appliance state with confirmation."""
        appliance = self.get_object()
        old_state = appliance.state
        new_state = 1 if old_state == 0 else 0
        
        appliance.state = new_state
        appliance.save()
        
        # Record history
        ApplianceHistory.objects.create(
            appliance=appliance,
            previous_state=old_state,
            new_state=new_state,
            action='toggled',
            triggered_by='user',
            triggered_by_user=request.user
        )
        
        response_data = ApplianceSerializer(appliance).data
        response_data['confirmation'] = {
            'status': 'success',
            'message': f"Appliance toggled successfully",
            'confirmed_state': new_state,
            'appliance_id': str(appliance.id),
            'appliance_name': appliance.name
        }
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def set_state(self, request, pk=None):
        """Set appliance state or numeric value (for sliders/displays) with confirmation."""
        serializer = ApplianceToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        appliance = self.get_object()
        old_state = appliance.state
        old_value = appliance.value
        
        # Handle either state (for toggles) or value (for sliders/displays)
        if serializer.validated_data.get('value') is not None:
            # Numeric value for slider/display
            new_value = int(serializer.validated_data['value'])
            appliance.value = new_value
            appliance.state = 1 if new_value > 0 else 0
            action = f'set_to_{new_value}'
            message = f"Appliance '{appliance.name}' set to {new_value}"
            confirmed_value = new_value
        else:
            # Binary state for toggle
            new_state = int(serializer.validated_data['state'])
            appliance.state = new_state
            if appliance.value is None:
                appliance.value = new_state
            action = 'turned_on' if new_state == 1 else 'turned_off'
            message = f"Appliance '{appliance.name}' turned {'ON' if new_state == 1 else 'OFF'}"
            confirmed_value = new_state
        
        appliance.save()
        
        # Record history
        ApplianceHistory.objects.create(
            appliance=appliance,
            previous_state=old_state,
            new_state=appliance.state,
            action=action,
            triggered_by='user',
            triggered_by_user=request.user
        )
        
        response_data = ApplianceSerializer(appliance).data
        response_data['confirmation'] = {
            'status': 'success',
            'message': message,
            'confirmed_value': confirmed_value,
            'appliance_id': str(appliance.id),
            'appliance_name': appliance.name,
            'previous_value': old_value,
            'new_value': appliance.value
        }
        return Response(response_data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get appliance history."""
        appliance = self.get_object()
        history = ApplianceHistory.objects.filter(
            appliance=appliance
        ).order_by('-timestamp')[:50]
        
        serializer = ApplianceHistorySerializer(history, many=True)
        return Response(serializer.data)


class DeviceFirmwareViewSet(viewsets.ModelViewSet):
    """ViewSet for firmware management."""
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceFirmwareSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device_type', 'status']
    search_fields = ['version', 'changelog']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return DeviceFirmware.objects.filter(status__in=['stable', 'testing'])
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest firmware for each device type."""
        device_types = Device.DEVICE_TYPE_CHOICES
        latest_versions = {}
        
        for device_type, _ in device_types:
            firmware = DeviceFirmware.objects.filter(
                device_type=device_type,
                status='stable'
            ).latest('created_at')
            latest_versions[device_type] = DeviceFirmwareSerializer(firmware).data if firmware else None
        
        return Response(latest_versions)
