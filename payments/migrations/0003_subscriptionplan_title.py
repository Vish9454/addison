# Generated by Django 3.2.5 on 2021-09-14 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_subscriptionplan_usersubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='title',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
