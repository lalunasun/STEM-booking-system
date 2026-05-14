from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0033_courseadjustment_makeup_eligibility'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrialRequest',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('scheduled', 'Scheduled'), ('canceled', 'Canceled')], default='pending', max_length=20)),
                ('parent_note', models.TextField(blank=True, max_length=1000, null=True)),
                ('admin_note', models.TextField(blank=True, max_length=1000, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_time', models.DateTimeField(auto_now=True, null=True)),
                ('child', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trial_requests', to='CSAA.child')),
                ('coding_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_coding_requests', to='CSAA.thing')),
                ('math_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_math_requests', to='CSAA.thing')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trial_requests', to='CSAA.user')),
                ('robotics_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_robotics_requests', to='CSAA.thing')),
            ],
            options={
                'db_table': 'b_trial_request',
            },
        ),
    ]
