from django.db import models
from accounts.models import User
from core.models import BaseModel


# Create your models here.


class Customers(BaseModel):
    """
        Model to map Customers
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customers")
    stripe_customer_id = models.CharField(max_length=30)


class CustomerCards(BaseModel):
    """
        Model to map Customer Cards
    """
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="cards")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customers_cards")
    card_id = models.CharField(max_length=50)
    fingerprint = models.CharField(max_length=30)


# class SubscriptionPlan(BaseModel):
#     """
#     Admin will be adding subscription plans
#     """
#     # Stripe end parameters
#     plan_id = models.CharField(null=True, blank=True, max_length=30)
#     product = models.CharField(null=True, blank=True, max_length=30)
#     amount = models.FloatField(null=True, blank=True, verbose_name='Amount')
#     currency = models.CharField(null=True, blank=True, max_length=10)
#     interval = models.CharField(null=True, blank=True, max_length=30)
#     title = models.CharField(null=True, blank=True, max_length=30)
#     interval_count = models.IntegerField(null=True, blank=True, verbose_name="cycle for billing")
#
#     class Meta:
#         verbose_name = 'SubscriptionPlan'
#         verbose_name_plural = 'SubscriptionPlans'
#
#
# class UserSubscription(BaseModel):
#     """
#         UserSubscription model used to save the User Subscription Detail.
#     """
#     user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='user_subscription',
#                                 null=True)
#     is_stripe_customer = models.BooleanField('StripeCustomer', default=False)
#     is_subscribed = models.BooleanField('Subscribed User', default=False)
#     subscription_start = models.DateTimeField(null=True, blank=True, verbose_name='Subscription Start')
#     subscription_end = models.DateTimeField(null=True, blank=True, verbose_name='Subscription End')
#     subscription_interval = models.CharField(max_length=20, null=True, blank=True, verbose_name='Subscription Interval')
#     ACTIVE = 1
#     INACTIVE = 2
#     SUBSCRIPTION_STATUS_C = (
#         (ACTIVE, 'Active'),
#         (INACTIVE, 'Inactive'),
#     )
#     subscription_status = models.IntegerField('Subscription status', choices=SUBSCRIPTION_STATUS_C, default=INACTIVE)
#     is_free = models.BooleanField('Free Access', default=False)
#     is_trial = models.BooleanField('Trial Access', default=False)
#     trial_end = models.DateTimeField(null=True, blank=True, verbose_name='Trial End')
#     subscription_id = models.CharField(max_length=30, null=True, blank=True)
#     plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, related_name="subscription_plan", null=True,
#                              blank=True)
#
#     class Meta:
#         verbose_name = 'UserSubscription'
#         verbose_name_plural = 'UserSubscriptions'


class InAppPurchase(BaseModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='user_subscription', null=True)
    is_subscribed = models.BooleanField('Subscribed User', default=False)
    subscription_start = models.DateTimeField(null=True, blank=True, verbose_name='Subscription Start')
    subscription_end = models.DateTimeField(null=True, blank=True, verbose_name='Subscription End')
    interval = models.CharField(max_length=20, null=True, blank=True, verbose_name='Interval In Months')
    # interval is taken for , when the "renew subscription" is done then we have to get the
    # interval of the subscription to update the subscription_end date.
    # for ios
    transition_id = models.TextField(null=True, blank=True)
    original_transition_id = models.TextField(null=True, blank=True)
    product_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='product id')
    # for android
    purchase_token = models.TextField(null=True, blank=True)
