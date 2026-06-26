from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CSAA', '0038_dailystudentadjustment'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentComment',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2000)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_student_comments', to='CSAA.user')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_comments', to='CSAA.child')),
            ],
            options={
                'db_table': 'b_student_comment',
            },
        ),
        migrations.AddIndex(
            model_name='studentcomment',
            index=models.Index(fields=['student', '-created_time'], name='b_student_c_student_d9bd8c_idx'),
        ),
    ]
