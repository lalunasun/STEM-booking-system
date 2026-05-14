from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0034_trialrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='trialrequest',
            name='coding_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_coding_requests', to='CSAA.order'),
        ),
        migrations.AddField(
            model_name='trialrequest',
            name='math_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_math_requests', to='CSAA.order'),
        ),
        migrations.AddField(
            model_name='trialrequest',
            name='robotics_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_robotics_requests', to='CSAA.order'),
        ),
    ]
