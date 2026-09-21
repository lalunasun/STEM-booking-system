from django.db import migrations


def seed_course_catalog(apps, schema_editor):
    Course = apps.get_model('CSAA', 'Course')
    for title in ['WeDo', 'VEX IQ', 'Spark Maths']:
        Course.objects.get_or_create(title=title)


class Migration(migrations.Migration):
    dependencies = [
        ('CSAA', '0052_course'),
    ]

    operations = [
        migrations.RunPython(seed_course_catalog, migrations.RunPython.noop),
    ]
