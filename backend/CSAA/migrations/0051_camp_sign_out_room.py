from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0050_campwaiver'),
    ]

    operations = [
        migrations.AddField(
            model_name='campattendance',
            name='sign_out_room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='camp_sign_out_attendance_records', to='CSAA.tag'),
        ),
        migrations.AddField(
            model_name='campenrollment',
            name='sign_out_room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='camp_sign_out_enrollments', to='CSAA.tag'),
        ),
    ]
