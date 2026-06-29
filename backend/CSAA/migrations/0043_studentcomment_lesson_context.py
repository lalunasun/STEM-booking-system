from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0042_child_gender_remark'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentcomment',
            name='lesson',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='student_comments',
                to='CSAA.lesson',
            ),
        ),
        migrations.AddField(
            model_name='studentcomment',
            name='lesson_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='studentcomment',
            index=models.Index(
                fields=['lesson', 'lesson_date', 'student'],
                name='b_student_c_lesson_086d8d_idx',
            ),
        ),
    ]
