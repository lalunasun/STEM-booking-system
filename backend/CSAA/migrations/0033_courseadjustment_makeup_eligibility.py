from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0032_courseadjustment'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseadjustment',
            name='source_adjustment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='makeup_records', to='CSAA.courseadjustment'),
        ),
        migrations.AlterField(
            model_name='courseadjustment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('makeup_available', 'Makeup Available'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=20),
        ),
    ]
