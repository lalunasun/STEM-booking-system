from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0039_studentcomment'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermanentCourseChange',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('effective_date', models.DateField()),
                ('original_source_return_time', models.DateTimeField()),
                ('transferred_lesson_count', models.PositiveIntegerField(default=0)),
                ('reason', models.CharField(blank=True, default='', max_length=500)),
                ('status', models.CharField(choices=[('active', 'Active'), ('reverted', 'Reverted')], default='active', max_length=20)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('reverted_time', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_permanent_course_changes', to='CSAA.user')),
                ('reverted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reverted_permanent_course_changes', to='CSAA.user')),
                ('source_lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_changes_out', to='CSAA.lesson')),
                ('source_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_changes_out', to='CSAA.order')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_course_changes', to='CSAA.child')),
                ('target_lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_changes_in', to='CSAA.lesson')),
                ('target_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permanent_changes_in', to='CSAA.order')),
            ],
            options={'db_table': 'b_permanent_course_change'},
        ),
        migrations.AddIndex(
            model_name='permanentcoursechange',
            index=models.Index(fields=['student', 'status'], name='b_perm_chg_student_status_idx'),
        ),
        migrations.AddIndex(
            model_name='permanentcoursechange',
            index=models.Index(fields=['effective_date', 'status'], name='b_perm_chg_date_status_idx'),
        ),
    ]
