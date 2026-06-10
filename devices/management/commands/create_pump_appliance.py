"""
Management command to create pump appliance for water monitoring devices.
"""
from django.core.management.base import BaseCommand
from devices.models import Device, Appliance

class Command(BaseCommand):
    help = 'Create pump appliance for water monitoring devices'

    def handle(self, *args, **options):
        # Find all water monitoring devices
        water_devices = Device.objects.filter(device_role='water_monitor')
        
        if not water_devices.exists():
            self.stdout.write(self.style.WARNING('No water monitoring devices found'))
            return
        
        for device in water_devices:
            # Check if pump appliance already exists
            pump_exists = Appliance.objects.filter(
                device=device, 
                appliance_type='pump'
            ).exists()
            
            if pump_exists:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Pump already exists for {device.device_name}')
                )
                continue
            
            # Create pump appliance
            pump = Appliance.objects.create(
                device=device,
                name='Water Pump',
                appliance_type='pump',
                pin='V0',
                virtual_pin='V0',
                state=0,
                icon='fa-faucet'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created pump appliance for {device.device_name} (ID: {pump.id})'
                )
            )
