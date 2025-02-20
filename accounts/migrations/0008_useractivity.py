# Generated by Django 3.2.5 on 2021-08-26 05:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20210825_0754'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Updated At')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Is Deleted')),
                ('activity_type', models.IntegerField(choices=[(1, 'Admin accepts the meeting'), (2, 'Admin rejects the meeting'), (3, 'Admin reschedules the meeting'), (4, 'Admin sends feeback')], verbose_name='Activity Type')),
                ('title', models.CharField(blank=True, max_length=100, null=True, verbose_name='title')),
                ('message', models.CharField(blank=True, max_length=100, null=True, verbose_name='message')),
                ('payload', models.CharField(blank=True, max_length=600, null=True, verbose_name='payload')),
                ('is_read', models.BooleanField(default=False, verbose_name='isread')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_receiver', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_sender', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'BaseModel',
                'abstract': False,
                'index_together': {('created_at', 'updated_at')},
            },
        ),
    ]
