from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0058_flexible_admin_trial_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomcoursepermission',
            name='blocked_days',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
