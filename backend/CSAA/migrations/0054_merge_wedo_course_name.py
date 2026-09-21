from django.db import migrations


def merge_wedo_names(apps, schema_editor):
    Course = apps.get_model('CSAA', 'Course')
    Thing = apps.get_model('CSAA', 'Thing')
    canonical, _ = Course.objects.get_or_create(title='WeDo')
    Thing.objects.filter(title__iexact='Wedo').update(title='WeDo')
    Course.objects.filter(title__iexact='Wedo').exclude(pk=canonical.pk).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('CSAA', '0053_seed_course_catalog'),
    ]

    operations = [
        migrations.RunPython(merge_wedo_names, migrations.RunPython.noop),
    ]
