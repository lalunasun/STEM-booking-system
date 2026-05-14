from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0035_trialrequest_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='trialrequest',
            name='package_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trial_package_requests', to='CSAA.order'),
        ),
    ]
