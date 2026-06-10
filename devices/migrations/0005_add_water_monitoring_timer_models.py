# Generated manually to add water monitoring and pump timer models.

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0004_appliance_value_alter_appliance_appliance_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaterMonitoringData',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('water_percentage', models.FloatField(help_text='Water level percentage (0-100)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('tds', models.FloatField(help_text='Total Dissolved Solids in ppm')),
                ('ph', models.FloatField(help_text='pH value (0-14)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(14)])),
                ('temperature', models.FloatField(help_text='Water temperature in Celsius')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='water_data', to='devices.device')),
            ],
            options={
                'ordering': ['-timestamp'],
                'verbose_name': 'Water Monitoring Data',
                'verbose_name_plural': 'Water Monitoring Data',
            },
        ),
        migrations.CreateModel(
            name='WaterPumpTimer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('hours', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)])),
                ('minutes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(59)])),
                ('seconds', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(59)])),
                ('is_active', models.BooleanField(default=False)),
                ('is_running', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('started_at', models.DateTimeField(blank=True, help_text='When the timer was last started', null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pump_timers', to='devices.device')),
            ],
            options={
                'ordering': ['-updated_at'],
                'verbose_name': 'Water Pump Timer',
                'verbose_name_plural': 'Water Pump Timers',
            },
        ),
        migrations.AddIndex(
            model_name='watermonitoringdata',
            index=models.Index(fields=['device', '-timestamp'], name='devices_wmd_device__0f4d25_idx'),
        ),
    ]
