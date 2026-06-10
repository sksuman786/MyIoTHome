# Generated manually to add device role field for dedicated water monitoring devices.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0007_otaupdate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='device_role',
            field=models.CharField(
                choices=[('standard', 'Standard'), ('water_monitor', 'Water Monitor')],
                default='standard',
                max_length=20,
                help_text='Designates the device role, such as a dedicated water monitoring device.',
            ),
        ),
    ]
