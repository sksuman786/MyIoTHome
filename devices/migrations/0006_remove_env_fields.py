# Generated migration to remove environmental fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_add_water_monitoring_timer_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='temperature',
        ),
        migrations.RemoveField(
            model_name='device',
            name='humidity',
        ),
        migrations.RemoveField(
            model_name='devicedata',
            name='temperature',
        ),
        migrations.RemoveField(
            model_name='devicedata',
            name='humidity',
        ),
        migrations.RemoveField(
            model_name='devicedata',
            name='pressure',
        ),
    ]
