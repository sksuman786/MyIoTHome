from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta

from devices.models import Device
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class Command(BaseCommand):
    help = 'Check device heartbeats and mark offline devices'

    def _broadcast(self, device):
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

    def handle(self, *args, **options):
        devices = Device.objects.filter(is_active=True)
        changed = 0
        for device in devices:
            if not device.last_heartbeat:
                if device.status != 'offline':
                    device.status = 'offline'
                    device.save(update_fields=['status'])
                    changed += 1
                    self._broadcast(device)
                continue

            delta = now() - device.last_heartbeat
            timeout = timedelta(seconds=(device.heartbeat_timeout_seconds or 50))

            if delta > timeout:
                if device.status != 'offline':
                    device.status = 'offline'
                    device.save(update_fields=['status'])
                    changed += 1
                    try:
                        from notifications.utils import send_device_status_notification
                        send_device_status_notification(device.user, device, device.status)
                    except Exception:
                        pass
                    self._broadcast(device)
            else:
                if device.status != 'online':
                    device.status = 'online'
                    device.save(update_fields=['status'])
                    changed += 1
                    try:
                        from notifications.utils import send_device_status_notification
                        send_device_status_notification(device.user, device, device.status)
                    except Exception:
                        pass
                    self._broadcast(device)

        self.stdout.write(self.style.SUCCESS(f'Checked {devices.count()} devices, updated {changed} devices.'))
