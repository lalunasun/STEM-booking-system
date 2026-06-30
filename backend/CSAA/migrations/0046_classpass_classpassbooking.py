from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0045_user_allow_class_pass'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassPass',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(default='Class Pass', max_length=100)),
                ('total_sessions', models.PositiveIntegerField(default=0)),
                ('used_sessions', models.PositiveIntegerField(default=0)),
                ('valid_from', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('expired', 'Expired'), ('canceled', 'Canceled')], default='active', max_length=20)),
                ('note', models.TextField(blank=True, default='', max_length=1000)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_passes', to='CSAA.child')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_class_passes', to='CSAA.user')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_passes', to='CSAA.user')),
            ],
            options={
                'db_table': 'b_class_pass',
            },
        ),
        migrations.CreateModel(
            name='ClassPassBooking',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('requested_date', models.DateField()),
                ('parent_note', models.TextField(blank=True, default='', max_length=1000)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=20)),
                ('admin_note', models.TextField(blank=True, default='', max_length=1000)),
                ('reviewed_time', models.DateTimeField(blank=True, null=True)),
                ('completed_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_pass_bookings', to='CSAA.child')),
                ('class_pass', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='CSAA.classpass')),
                ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_class_pass_bookings', to='CSAA.user')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_pass_bookings', to='CSAA.user')),
                ('requested_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_class_pass_bookings', to='CSAA.thing')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_class_pass_bookings', to='CSAA.user')),
                ('target_lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='class_pass_bookings', to='CSAA.lesson')),
            ],
            options={
                'db_table': 'b_class_pass_booking',
            },
        ),
        migrations.AddIndex(
            model_name='classpass',
            index=models.Index(fields=['parent', 'child', 'status'], name='b_class_pass_parent_child_idx'),
        ),
        migrations.AddIndex(
            model_name='classpassbooking',
            index=models.Index(fields=['parent', 'status'], name='b_class_booking_parent_idx'),
        ),
        migrations.AddIndex(
            model_name='classpassbooking',
            index=models.Index(fields=['target_lesson', 'requested_date', 'status'], name='b_class_booking_lesson_idx'),
        ),
    ]
