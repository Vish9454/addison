# Generated by Django 3.2.5 on 2021-08-12 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20210723_0958'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='full_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Full Name'),
        ),
    ]
