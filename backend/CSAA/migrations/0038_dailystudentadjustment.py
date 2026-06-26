from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0037_studentlessonnote'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyStudentAdjustment',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('lesson_date', models.DateField()),
                ('adjustment_type', models.CharField(choices=[('move', 'Move'), ('sick_leave', 'Sick Leave')], max_length=20)),
                ('lesson_count_delta', models.IntegerField(default=0)),
                ('reason', models.CharField(blank=True, default='', max_length=300)),
                ('status', models.CharField(choices=[('active', 'Active'), ('reverted', 'Reverted')], default='active', max_length=20)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('reverted_time', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_daily_adjustments', to='CSAA.user')),
                ('reverted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reverted_daily_adjustments', to='CSAA.user')),
                ('source_lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_adjustments_out', to='CSAA.lesson')),
                ('source_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_adjustments', to='CSAA.order')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_adjustments', to='CSAA.child')),
                ('target_lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daily_adjustments_in', to='CSAA.lesson')),
            ],
            options={
                'db_table': 'b_daily_student_adjustment',
            },
        ),
        migrations.AddIndex(
            model_name='dailystudentadjustment',
            index=models.Index(fields=['lesson_date', 'status'], name='b_daily_stu_lesson__4246d1_idx'),
        ),
        migrations.AddIndex(
            model_name='dailystudentadjustment',
            index=models.Index(fields=['student', 'lesson_date'], name='b_daily_stu_student_7f6588_idx'),
        ),
    ]
