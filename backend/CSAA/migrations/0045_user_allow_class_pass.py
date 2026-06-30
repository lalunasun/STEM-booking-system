from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0044_studentattendance'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='allow_class_pass',
            field=models.BooleanField(default=False),
        ),
    ]
