"""
WebSocket consumers for real-time updates using Django Channels.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from devices.models import Device, Appliance, DeviceData


class DeviceStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time device status updates.
    
    Connect URL: ws://localhost:8000/ws/devices/
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a unique room for each user
        self.room_name = f"user_{self.user.id}_devices"
        self.room_group_name = f"devices_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial status
        devices_status = await self.get_user_devices_status()
        await self.send(text_data=json.dumps({
            'type': 'initial_status',
            'devices': devices_status
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            
            elif message_type == 'get_status':
                devices_status = await self.get_user_devices_status()
                await self.send(text_data=json.dumps({
                    'type': 'devices_status',
                    'devices': devices_status
                }))
            
            elif message_type == 'subscribe_device':
                device_id = data.get('device_id')
                await self.subscribe_device(device_id)
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def device_status_update(self, event):
        """Handle device status update message from group."""
        await self.send(text_data=json.dumps(event['data']))
    
    async def appliance_state_change(self, event):
        """Handle appliance state change message from group."""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_user_devices_status(self):
        """Get current status of all user devices."""
        if self.user.role == 'admin':
            devices = Device.objects.all()
        else:
            devices = Device.objects.filter(user=self.user)
        
        devices_data = []
        for device in devices:
            devices_data.append({
                'id': str(device.id),
                'device_id': device.device_id,
                'device_name': device.device_name,
                'status': device.status,
                'online': device.is_online(),
                'wifi_signal': device.wifi_signal,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                'appliances': [
                    {
                        'id': str(app.id),
                        'name': app.name,
                        'state': app.state,
                        'virtual_pin': app.virtual_pin,
                        'icon': app.icon,
                    } for app in device.appliances.filter(is_active=True)
                ]
            })
        
        return devices_data
    
    @database_sync_to_async
    def subscribe_device(self, device_id):
        """Subscribe to a specific device."""
        try:
            device = Device.objects.get(id=device_id)
            if device.user == self.user or self.user.role == 'admin':
                self.device_id = device_id
        except Device.DoesNotExist:
            pass


class ApplianceControlConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time appliance control.
    
    Connect URL: ws://localhost:8000/ws/appliances/
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_name = f"user_{self.user.id}_appliances"
        self.room_group_name = f"appliances_{self.room_name}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive control command."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'toggle_appliance':
                appliance_id = data.get('appliance_id')
                await self.toggle_appliance(appliance_id)
            
            elif message_type == 'set_appliance_state':
                appliance_id = data.get('appliance_id')
                state = data.get('state')
                await self.set_appliance_state(appliance_id, state)
        
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def appliance_state_changed(self, event):
        """Handle appliance state change."""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def toggle_appliance(self, appliance_id):
        """Toggle appliance state."""
        try:
            from devices.models import ApplianceHistory
            appliance = Appliance.objects.get(id=appliance_id)
            
            # Check permissions
            if appliance.device.user != self.user and self.user.role != 'admin':
                return
            
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
                triggered_by_user=self.user
            )
            
            return True
        except Appliance.DoesNotExist:
            return False
    
    @database_sync_to_async
    def set_appliance_state(self, appliance_id, state):
        """Set appliance state."""
        try:
            from devices.models import ApplianceHistory
            appliance = Appliance.objects.get(id=appliance_id)
            
            # Check permissions
            if appliance.device.user != self.user and self.user.role != 'admin':
                return
            
            old_state = appliance.state
            appliance.state = int(state)
            appliance.save()
            
            # Record history
            action = 'turned_on' if state == 1 else 'turned_off'
            ApplianceHistory.objects.create(
                appliance=appliance,
                previous_state=old_state,
                new_state=int(state),
                action=action,
                triggered_by='user',
                triggered_by_user=self.user
            )
            
            return True
        except Appliance.DoesNotExist:
            return False
