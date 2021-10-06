# Generated by Django 3.2.5 on 2021-09-27 05:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0004_subscriptionplan_interval_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='InAppPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Updated At')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Is Deleted')),
                ('is_subscribed', models.BooleanField(default=False, verbose_name='Subscribed User')),
                ('subscription_start', models.DateTimeField(blank=True, null=True, verbose_name='Subscription Start')),
                ('subscription_end', models.DateTimeField(blank=True, null=True, verbose_name='Subscription End')),
                ('interval', models.CharField(blank=True, max_length=20, null=True, verbose_name='Interval In Months')),
                ('transition_id', models.TextField(blank=True, null=True)),
                ('original_transition_id', models.TextField(blank=True, null=True)),
                ('product_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='product id')),
                ('purchase_token', models.TextField(blank=True, null=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_subscription', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'BaseModel',
                'abstract': False,
                'index_together': {('created_at', 'updated_at')},
            },
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='user',
        ),
        migrations.DeleteModel(
            name='SubscriptionPlan',
        ),
        migrations.DeleteModel(
            name='UserSubscription',
        ),
    ]
