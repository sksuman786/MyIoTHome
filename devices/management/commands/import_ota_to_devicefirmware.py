from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone

from devices.models import OTAUpdate, DeviceFirmware


class Command(BaseCommand):
    help = 'Import OTAUpdate records into DeviceFirmware entries (for admin view)'

    def handle(self, *args, **options):
        created = 0
        for ota in OTAUpdate.objects.all():
            try:
                # Skip if checksum already imported
                if DeviceFirmware.objects.filter(checksum=ota.checksum).exists():
                    self.stdout.write(f"Skipping {ota.id} (already imported)")
                    continue

                # Determine device_type from OTA device
                device_type = getattr(ota.device, 'device_type', 'Other')

                # Ensure unique version (DeviceFirmware.version is unique)
                base_version = ota.version or 'v0'
                version = base_version
                suffix = 1
                while DeviceFirmware.objects.filter(version=version).exists():
                    version = f"{base_version}-{suffix}"
                    suffix += 1

                # Read binary content
                bin_file = ota.bin_file
                bin_file.open('rb')
                data = bin_file.read()
                bin_file.close()

                filename = f"{ota.id}_{ota.version}.bin" if ota.version else f"{ota.id}.bin"
                storage_path = f"firmware/{filename}"

                # Create DeviceFirmware record
                firmware = DeviceFirmware()
                firmware.version = version
                firmware.device_type = device_type
                firmware.file.save(storage_path, ContentFile(data), save=False)
                firmware.file_size = ota.file_size or len(data)
                firmware.checksum = ota.checksum or ''
                firmware.changelog = ota.notes or 'Imported from OTAUpdate'
                firmware.release_notes = ota.notes or ''
                # Map OTA status to firmware status
                status_map = {
                    'pending': 'testing',
                    'downloading': 'testing',
                    'completed': 'stable',
                    'failed': 'deprecated'
                }
                firmware.status = status_map.get(ota.status, 'draft')
                firmware.released_at = ota.created_at or timezone.now()
                firmware.save()

                created += 1
                self.stdout.write(f"Imported OTA {ota.id} as DeviceFirmware {firmware.id}")
            except Exception as e:
                self.stderr.write(f"Failed to import {ota.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Import complete — {created} firmware(s) created"))
