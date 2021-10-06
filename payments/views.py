from django.shortcuts import render
import stripe
import pytz
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework import status as status_code
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.models import User
from config.local import STRIPE_SECRET_KEY
from core.exception import get_custom_error, CustomException
from core.messages import success_message, validation_message
from core.pagination import CustomPagination
from core.permissions import IsUser, IsAdmin
from core import utils as core_utils
from core.authentication import CustomTokenAuthentication
from config.local import INAPP_IOS_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY
from rest_framework import mixins, viewsets
from payments.stripe_methods import Stripe
from core.response import SuccessResponse
from rest_framework.permissions import IsAuthenticated
import logging
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)

# from payments.stripe_methods import stripe_plan_create, plan_change, update_users_for_subscription
"""DB import"""
from accounts.models import ScheduleMeeting
from payments.models import Customers, CustomerCards, InAppPurchase

"""Serializer import"""


class CreateStripeCustomer(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        customer_obj = Customers.objects.filter(user_id=request.user.id, stripe_customer_id__isnull=False).first()
        if customer_obj:
            stripe_customer_detail = stripe.Customer.retrieve(customer_obj.stripe_customer_id)
            return SuccessResponse(stripe_customer_detail, status=status_code.HTTP_200_OK)
            # return Response(get_custom_error(message=validation_message.get('CUSTOMER_ALREADY_EXISTS'),
            #                                  error_location='stripe_customer', status=400),
            #                 status=status_code.HTTP_400_BAD_REQUEST)
        # calling the stripe constructor
        # stripe is object of the class Stripe
        # reponse is the calling of method with the object
        try:
            stripe_call = Stripe(request.user.id)
            response = stripe_call.stripe_customer_create()
            customer_obj = Customers.objects.create(user_id=request.user.id, stripe_customer_id=response.id)
            # customer_obj.user.user_subscription.is_stripe_customer = True
            # customer_obj.user.user_subscription.save()
            return SuccessResponse(response, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('ERROR_CREATING_CUSTOMER'),
                                             error_location='stripe_customer', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)


class Card(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin,
           viewsets.GenericViewSet):
    """
    Add,list and delete customer card
    """
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        """adding customer stripe card"""
        try:
            card_token = request.query_params.get('card_token')
            stripe_obj = Stripe(request.user.id)
            stripe_card = stripe_obj.stripe_create_card(card_token)

            # to remove duplicacy of customer cards
            card_obj = CustomerCards.objects.filter(user=request.user.id, fingerprint=stripe_card.fingerprint).first()
            if card_obj:
                stripe.Customer.delete_source(request.user.customers.first().stripe_customer_id, stripe_card.id)
                return Response(get_custom_error(message=validation_message.get('CARD_EXISTS'),
                                                 error_location='Create Card', status=400),
                                status=status_code.HTTP_400_BAD_REQUEST)
            CustomerCards.objects.create(
                customer=request.user.customers.first(),
                user=request.user,
                card_id=stripe_card.id,
                fingerprint=stripe_card.fingerprint
            )
            return SuccessResponse({"message": success_message.get('CARD_ADDED'),
                                    }, status=status_code.HTTP_200_OK)
        except Exception as ex:
            print(ex)
            msg = core_utils.create_exception_message(ex)
            # return Response(get_custom_error(message=validation_message.get('ERROR_ADDING_CARD'),
            return Response(get_custom_error(message=msg,
                                             error_location='Create Card', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        try:
            stripe = Stripe(request.user.id)
            stripe_card = stripe.stripe_list_card()
            return SuccessResponse(stripe_card, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('ERROR_LISTING_CARD'),
                                             error_location='list Card', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        card_id = request.query_params.get('card_id')
        if not card_id:
            return Response(get_custom_error(message=validation_message.get('CARD_ERROR'),
                                             error_location='delete Card', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        try:
            stripe = Stripe(request.user.id)
            stripe_obj = stripe.stripe_delete_card(card_id)
            if stripe_obj == True:
                CustomerCards.objects.filter(card_id=card_id).delete()
                return SuccessResponse({"message": success_message.get('CARD_DELETE_SUCSSES'),
                                        }, status=status_code.HTTP_200_OK)
        except Exception as ex:
            msg = core_utils.create_exception_message(ex)
            # return Response(get_custom_error(message=validation_message.get('ERROR_DELETE_CARD'),
            return Response(get_custom_error(message=msg,
                                             error_location='delete Card', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)


class IntentPaymentOperations(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet,
                              mixins.UpdateModelMixin):
    permission_classes = (IsUser,)
    """
    here let us suppose the payment intent is created. 

    And patient cancels the booking , 
    2-If the booking is cancelled within 24 hrs of visit_start_time then --
    Firstly the amount and payment_intent_id is passed in the modify payment and amount is changed to 
    (deducting the cancellation charge) cancellation charge and then confirm payment API is hit to 
    pay the cancellation charge to the admin

    2- If the visit_start_time > 24 hrs then the cancellation charge is 0 then cancel_payment API is called.

    3- If the booking has state=4 then confirm_payment API is called 
    """

    def create(self, request, *args, **kwargs):
        # process to keep the co_pay on hold (amount will be deducted from patients acc, but not credited to Admin)
        booking_id = request.query_params.get("booking_id")
        currency = request.query_params.get("currency")
        amount = request.query_params.get("amount")
        card_id = request.query_params.get("card_id")
        if not booking_id or not currency or not card_id:
            return Response(get_custom_error(message=validation_message.get('ID_CURRENCY_CARD'),
                                             error_location='create hold payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        if ScheduleMeeting.objects.filter(id=booking_id, payment_intent_id__isnull=False).exists():
            return Response(get_custom_error(message=validation_message.get('PAYMENT_CREATED_ALREADY'),
                                             error_location='create hold payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        # calling constructor
        # try:
        stripe_obj = Stripe(request.user.id)
        stripe_pay = stripe_obj.create_payment_intent(booking_id, currency, amount, card_id)
        ScheduleMeeting.objects.filter(id=booking_id).update(state=3, payment_intent_id=stripe_pay.id)
        return SuccessResponse(stripe_pay, status=status_code.HTTP_200_OK)
        # except Exception:
        #     return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
        #                                      error_location='create hold payment', status=400),
        #                     status=status_code.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        try:
            stripe = Stripe(request.user.id)
            stripe_payment_list = stripe.list_payment_intent()
            return SuccessResponse(stripe_payment_list, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
                                             error_location='list payments', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)

    def update(self, request):
        """
        This is the confirm payment when the booking is at state=4 and amount is in payment intent
        """
        booking_id = request.query_params.get("booking_id")
        payment_intent_id = ScheduleMeeting.objects.get(id=booking_id).payment_intent_id
        card_id = ScheduleMeeting.objects.get(id=booking_id).card_id
        if not payment_intent_id or not card_id:
            return Response(get_custom_error(message=validation_message.get('INTENT_CARD_BOOKING_ID'),
                                             error_location='confirm payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        try:
            stripe_obj = Stripe(request.user.id)
            stripe_payment_confirm = stripe_obj.confirm_payment_intent(payment_intent_id, card_id)
            ScheduleMeeting.objects.filter(id=booking_id).update(state=4)
            return SuccessResponse(stripe_payment_confirm, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
                                             error_location='confirm payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)

    def retrieve(self, request):
        payment_intent_id = request.query_params.get("payment_intent_id")
        if not payment_intent_id:
            return Response(get_custom_error(message=validation_message.get('PAYMENT_INTENT_ID'),
                                             error_location='retrieve payment info', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        # calling constructor
        try:
            stripe_obj = Stripe(request.user.id)
            stripe_retrieve = stripe_obj.retrieve_payment_intent(payment_intent_id)
            return SuccessResponse(stripe_retrieve, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
                                             error_location='retrieve payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)


class ModifyPaymentIntent(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = (IsUser,)

    def update(self, request):
        """
        This is the update the amount of payment if the booking has to be cancelled
        In the amount the cancellation charge will come
        """
        payment_intent_id = request.query_params.get("payment_intent_id")
        amount = request.query_params.get("amount")
        amount = int(amount) * 100
        if not payment_intent_id or not amount:
            return Response(get_custom_error(message=validation_message.get('PAYMENT_AMOUNT'),
                                             error_location='modify payment intent', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        try:
            stripe_obj = Stripe(request.user.id)
            stripe_payment_modify = stripe_obj.update_payment_intent(payment_intent_id, amount)
            return SuccessResponse(stripe_payment_modify, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
                                             error_location='modify payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)


class CancelPaymentIntent(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsUser,)

    def create(self, request, *args, **kwargs):
        payment_intent_id = request.query_params.get("payment_intent_id")
        if not payment_intent_id:
            return Response(get_custom_error(message=validation_message.get('PAYMENT_AMOUNT'),
                                             error_location='cancel payment intent', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
        # calling constructor
        try:
            stripe_obj = Stripe(request.user.id)
            stripe_cancel = stripe_obj.cancel_payment_intent(payment_intent_id)
            ScheduleMeeting.objects.filter(payment_intent_id=payment_intent_id).update(state=ScheduleMeeting.CANCEL)
            return SuccessResponse(stripe_cancel, status=status_code.HTTP_200_OK)
        except Exception:
            return Response(get_custom_error(message=validation_message.get('TRY_LATER'),
                                             error_location='cancel payment', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)


class BankAccount(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """class used for adding bank account to a admin account created in stripe"""
    permission_classes = (IsAdmin,)

    def create(self, request, *args, **kwargs):
        """create customer cards"""
        data = request.data
        # try:
        stripe_obj = Stripe(request.user.id)
        bank_account = stripe_obj.add_bankaccount(data)
        return SuccessResponse(bank_account, status=status_code.HTTP_200_OK)
        #
        # except Exception:
        #     return Response(get_custom_error(message=validation_message.get('BANK_ACCOUNT'),
        #                                      error_location='add bank', status=400),
        #                     status=status_code.HTTP_400_BAD_REQUEST)

    def list(self, request):
        stripe_obj = Stripe(request.user.id)
        bank_account = stripe_obj.retrieve_bankaccount()
        return SuccessResponse(bank_account, status=status_code.HTTP_200_OK)


class AdminAccount(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
        Class which will handle admin account
    """
    permission_classes = (IsAdmin,)

    def create(self, request):
        # try:
        # calling constructor
        stripe_obj = Stripe(request.user.id)
        response = stripe_obj.create_admin_account()
        admin_account = response.id
        # admin_account is stored in Customer -> stripe_customer_id
        Customers.objects.create(user=request.user, stripe_customer_id=admin_account)
        return SuccessResponse(response, status=status_code.HTTP_200_OK)

        # except Exception:
        #     return Response(get_custom_error(message=validation_message.get('ADMIN_ACCOUNT_ERROR'),
        #                                      error_location='create admin account', status=400),
        #                     status=status_code.HTTP_400_BAD_REQUEST)


# class PlansSubscriptionAdmin(viewsets.ViewSet):
#     permission_classes = (IsAdmin,)
#     pagination_class = CustomPagination
#     action_serializers = {
#         'list': ListSubscriptionSerializer,
#         'retrieve': ListSubscriptionSerializer,
#
#     }
#
#     def create(self, request):
#         """
#         post method used for the Subscription.
#             :param request:
#             :return: response
#         """
#         # try:
#         plan_obj = SubscriptionPlan.objects.filter(amount=request.data.get('amount'),
#                                                    currency=request.data.get('currency')).first()
#         if plan_obj:
#             return Response(get_custom_error(message=validation_message.get('PLAN_EXISTS'),
#                                              error_location=validation_message.get('SUBSCRIPTION_PLAN'),
#                                              status=400),
#                             status=status_code.HTTP_400_BAD_REQUEST)
#         stripe_plan = stripe_plan_create(request)
#         SubscriptionPlan.objects.create(plan_id=stripe_plan.id,
#                                         product=stripe_plan.product,
#                                         amount=request.data['amount'],
#                                         currency=request.data['currency'],
#                                         title=request.data['title'],
#                                         interval=request.data['interval'],
#                                         interval_count=request.data['interval_count']
#                                         )
#         return SuccessResponse({"message": success_message.get('PLAN_SUCCESSFUL')}, status=status_code.HTTP_200_OK)
#         # except Exception as ex:
#         #     print(ex)
#         #     msg = core_utils.create_exception_message(ex)
#         #     raise CustomException(status_code=400, message=msg, location="Plan creation")
#
#     def list(self, request):
#         """
#         list method used for sunbscription plan
#             :param request:
#             :return: response
#         """
#         sub_obj = SubscriptionPlan.objects.filter().all().order_by('created_at')
#         pagination_class = self.pagination_class()
#         page = pagination_class.paginate_queryset(sub_obj, request)
#         if page is not None:
#             serializer = self.action_serializers.get(self.action)(instance=page, many=True)
#             return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
#                                    status=status_code.HTTP_200_OK)
#         serializer = self.action_serializers.get(self.action)(sub_obj, many=True)
#         return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
#
#     def retrieve(self, request, plan_id):
#         """
#         retrieve method used for subscription plan
#             :param request:
#             :param plan_id:
#             :return: response
#         """
#         sub_obj = SubscriptionPlan.objects.filter(id=plan_id).first()
#         data = {}
#         if sub_obj:
#             serializer = self.action_serializers.get(self.action)(sub_obj)
#             data = serializer.data
#         return SuccessResponse(data, status=status_code.HTTP_200_OK)


class UpdatePurchaseTokenAndroid(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def update(self, request):
        user = request.user
        interval = request.data.get('interval')
        purchase_token = request.data.get("purchase_token")
        user_obj = User.objects.filter(id=user.id).first()
        if not user_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("USER_NOT_FOUND"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        if not purchase_token or not interval:
            return Response(get_custom_error(status=400, message=validation_message.get("PURCHASE_TOKEN"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        subscription_start = datetime.now()
        subscription_end = datetime.now() + relativedelta(months=int(interval))
        InAppPurchase.objects.update_or_create(user=request.user,
                                               defaults={
                                                   'purchase_token': purchase_token,
                                                   'interval': interval,
                                                   'is_subscribed': True,
                                                   'subscription_start': subscription_start,
                                                   'subscription_end': subscription_end,

                                               })
        return SuccessResponse({"message": success_message.get('DATA_SAVED')}, status=status_code.HTTP_200_OK)


class UpdateSubscriptionWebhookAndroid(viewsets.ViewSet):

    def update(self, request):
        message = request.data.get("message")
        data = message.get("data")
        response = core_utils.payment_on_android(data)
        return SuccessResponse(response, status=status_code.HTTP_200_OK)
