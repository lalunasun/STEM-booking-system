from django.db import migrations


def seed_time_slot(apps, schema_editor):
    Time = apps.get_model('CSAA', 'Time')
    Time.objects.get_or_create(time='17:30-19:00')


class Migration(migrations.Migration):
    dependencies = [
        ('CSAA', '0059_roomcoursepermission_blocked_days'),
    ]

    operations = [
        migrations.RunPython(seed_time_slot, migrations.RunPython.noop),
    ]
