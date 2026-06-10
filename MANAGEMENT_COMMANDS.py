"""
Management commands for MyHome IoT
"""

# Create this file at: myhome/accounts/management/commands/setup_demo.py

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from accounts.models import User, APIKey
from devices.models import Device, Appliance
import secrets
import string


class Command(BaseCommand):
    help = 'Setup demo data for MyHome IoT'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up demo data...'))
        
        # Create demo user
        if not User.objects.filter(username='demo').exists():
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123456',
                first_name='Demo',
                last_name='User',
                role='user',
                is_email_verified=True
            )
            self.stdout.write(f'✓ Created demo user: {user.username}')
        else:
            user = User.objects.get(username='demo')
        
        # Create demo device
        if not Device.objects.filter(device_id='ESP8266_DEMO').exists():
            device = Device.objects.create(
                user=user,
                device_id='ESP8266_DEMO',
                device_name='Demo Living Room',
                device_type='esp8266',
                status='online',
                firmware_version='1.0.0',
                ip_address='192.168.1.100',
                last_heartbeat=now()
            )
            self.stdout.write(f'✓ Created demo device: {device.device_name}')
            shared_key = user.get_or_create_api_key()
            self.stdout.write(f'  API Key: {shared_key.key}')
        else:
            device = Device.objects.get(device_id='ESP8266_DEMO')
        
        # Create demo appliances
        appliances_data = [
            {'name': 'Room1 Light', 'virtual_pin': 'V0', 'room': 'Room 1', 'icon': 'fa-lightbulb'},
            {'name': 'Room1 Fan', 'virtual_pin': 'V1', 'room': 'Room 1', 'icon': 'fa-fan'},
            {'name': 'Room1 Outer Light', 'virtual_pin': 'V2', 'room': 'Room 1', 'icon': 'fa-lightbulb'},
            {'name': 'Room1 Main Gate', 'virtual_pin': 'V3', 'room': 'Room 1', 'icon': 'fa-door-open'},
            {'name': 'Room3 Light', 'virtual_pin': 'V4', 'room': 'Room 3', 'icon': 'fa-lightbulb'},
            {'name': 'Room3 Fan', 'virtual_pin': 'V5', 'room': 'Room 3', 'icon': 'fa-fan'},
            {'name': 'Room3 Outside Light', 'virtual_pin': 'V6', 'room': 'Room 3', 'icon': 'fa-lightbulb'},
            {'name': 'Room3 Road Side Light', 'virtual_pin': 'V7', 'room': 'Room 3', 'icon': 'fa-lightbulb'},
        ]
        
        for app_data in appliances_data:
            if not Appliance.objects.filter(device=device, virtual_pin=app_data['virtual_pin']).exists():
                Appliance.objects.create(
                    device=device,
                    name=app_data['name'],
                    virtual_pin=app_data['virtual_pin'],
                    pin=app_data['virtual_pin'],
                    room=app_data['room'],
                    icon=app_data['icon'],
                    state=0,
                    can_control=True
                )
                self.stdout.write(f'✓ Created appliance: {app_data["name"]}')
        
        # Create API keys
        if not APIKey.objects.filter(user=user).exists():
            api_key = APIKey.objects.create(
                user=user,
                name='Demo Mobile App',
                can_read_devices=True,
                can_write_devices=True,
                can_read_data=True,
                can_write_data=True
            )
            self.stdout.write(f'✓ Created API Key: {api_key.name}')
            self.stdout.write(f'  Key: {api_key.key}')
        
        self.stdout.write(self.style.SUCCESS('\\n✓ Demo setup complete!'))
        self.stdout.write('\\nDemo Credentials:')
        self.stdout.write('  Username: demo')
        self.stdout.write('  Password: demo123456')
        self.stdout.write('  Email: demo@example.com')
