from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0036_trialrequest_package_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentLessonNote',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('lesson_date', models.DateField()),
                ('note', models.TextField(blank=True, default='', max_length=1000)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_student_lesson_notes', to='CSAA.user')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_notes', to='CSAA.lesson')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_notes', to='CSAA.child')),
            ],
            options={
                'db_table': 'b_student_lesson_note',
            },
        ),
        migrations.AddConstraint(
            model_name='studentlessonnote',
            constraint=models.UniqueConstraint(fields=('student', 'lesson', 'lesson_date'), name='unique_student_lesson_note'),
        ),
    ]
