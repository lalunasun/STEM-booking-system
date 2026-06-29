from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0043_studentcomment_lesson_context'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentAttendance',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('lesson_date', models.DateField()),
                ('is_absent', models.BooleanField(default=False)),
                ('marked_time', models.DateTimeField(auto_now=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='CSAA.lesson')),
                ('marked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marked_student_attendance', to='CSAA.user')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='CSAA.child')),
            ],
            options={
                'db_table': 'b_student_attendance',
            },
        ),
        migrations.AddConstraint(
            model_name='studentattendance',
            constraint=models.UniqueConstraint(fields=('student', 'lesson', 'lesson_date'), name='unique_student_lesson_attendance'),
        ),
        migrations.AddIndex(
            model_name='studentattendance',
            index=models.Index(fields=['lesson', 'lesson_date', 'student'], name='b_student_a_lesson_4ee607_idx'),
        ),
    ]
