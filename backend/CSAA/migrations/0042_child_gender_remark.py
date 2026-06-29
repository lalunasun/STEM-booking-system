from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0041_systemsetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='gender',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='child',
            name='remark',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]
