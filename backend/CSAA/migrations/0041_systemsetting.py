from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('CSAA', '0040_permanentcoursechange'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSetting',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.TextField(blank=True, default='')),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_system_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'b_system_setting',
            },
        ),
        migrations.AddIndex(
            model_name='systemsetting',
            index=models.Index(fields=['key'], name='b_system_setting_key_idx'),
        ),
    ]
