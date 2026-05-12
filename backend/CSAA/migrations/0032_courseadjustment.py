from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0031_auto_20241024_1536'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAdjustment',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('original_lesson_date', models.DateField(blank=True, null=True)),
                ('original_day', models.CharField(blank=True, max_length=10, null=True)),
                ('original_time', models.CharField(blank=True, max_length=50, null=True)),
                ('request_type', models.CharField(choices=[('cancel_class', 'Cancel Class'), ('makeup_class', 'Makeup Class'), ('admin_manual_reschedule', 'Admin Manual Reschedule')], default='cancel_class', max_length=40)),
                ('request_reason', models.TextField(blank=True, max_length=1000, null=True)),
                ('request_source', models.CharField(choices=[('parent', 'Parent'), ('admin', 'Admin')], default='parent', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=20)),
                ('recommended_options', models.TextField(blank=True, max_length=2000, null=True)),
                ('admin_extra_recommendation', models.TextField(blank=True, max_length=1000, null=True)),
                ('selected_target_date', models.DateField(blank=True, null=True)),
                ('selected_target_day', models.CharField(blank=True, max_length=10, null=True)),
                ('selected_target_time', models.CharField(blank=True, max_length=50, null=True)),
                ('selected_target_room', models.CharField(blank=True, max_length=100, null=True)),
                ('admin_note', models.TextField(blank=True, max_length=1000, null=True)),
                ('parent_note', models.TextField(blank=True, max_length=1000, null=True)),
                ('approved_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_time', models.DateTimeField(auto_now=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_course_adjustments', to='CSAA.user')),
                ('original_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_adjustments', to='CSAA.thing')),
                ('original_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_adjustments', to='CSAA.order')),
                ('original_term', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_adjustments', to='CSAA.term')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_adjustments', to='CSAA.user')),
                ('selected_target_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='target_course_adjustments', to='CSAA.thing')),
                ('student', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_adjustments', to='CSAA.child')),
            ],
            options={
                'db_table': 'b_course_adjustment',
            },
        ),
    ]
