from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0057_admin_trial_session'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admintrialsession',
            name='lesson',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='admin_trial_sessions',
                to='CSAA.lesson',
            ),
        ),
        migrations.AddField(
            model_name='admintrialsession',
            name='room',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='flexible_admin_trial_sessions',
                to='CSAA.tag',
            ),
        ),
        migrations.AddField(
            model_name='admintrialsession',
            name='course_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='admintrialsession',
            name='booking_mode',
            field=models.CharField(default='existing', max_length=20),
        ),
        migrations.AddField(
            model_name='admintrialsession',
            name='teacher_confirmation_required',
            field=models.BooleanField(default=False),
        ),
    ]
