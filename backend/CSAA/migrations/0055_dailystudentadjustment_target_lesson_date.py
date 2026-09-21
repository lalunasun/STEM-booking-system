from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0054_merge_wedo_course_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailystudentadjustment',
            name='target_lesson_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
