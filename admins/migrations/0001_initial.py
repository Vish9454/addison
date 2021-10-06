# Generated by Django 3.2.5 on 2021-07-23 09:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Updated At')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Is Deleted')),
                ('slots', models.DurationField(default=datetime.timedelta(0))),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
            ],
            options={
                'verbose_name': 'BaseModel',
                'abstract': False,
                'index_together': {('created_at', 'updated_at')},
            },
        ),
    ]
