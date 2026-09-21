from django.db import migrations, models


def seed_courses(apps, schema_editor):
    Course = apps.get_model('CSAA', 'Course')
    Thing = apps.get_model('CSAA', 'Thing')
    titles = Thing.objects.exclude(title__isnull=True).exclude(title='').values_list('title', flat=True).distinct()
    for title in titles:
        clean_title = str(title).strip()
        if clean_title:
            Course.objects.get_or_create(title=clean_title)


class Migration(migrations.Migration):
    dependencies = [
        ('CSAA', '0051_camp_sign_out_room'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, unique=True)),
                ('active', models.BooleanField(default=True)),
                ('create_time', models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={'db_table': 'b_course'},
        ),
        migrations.RunPython(seed_courses, migrations.RunPython.noop),
    ]
