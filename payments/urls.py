from django.conf.urls import url
from payments import views as payment_views
from django.urls import path

urlpatterns = [
    path("createstripecustomer", payment_views.CreateStripeCustomer.as_view({"post": "create"}), name="create stripe "
                                                                                                      "customer"),
    path("createliststripecard", payment_views.Card.as_view({"post": "create", "get": "list"}),
         name="create stripe card"),
    path("deletesrtipecard", payment_views.Card.as_view({"delete": "destroy"}), name="delete stripe card"),
    path("createholdpayment", payment_views.IntentPaymentOperations.as_view({"post": "create"}), name="create hold "
                                                                                                      "payment"),
    path("listpayments", payment_views.IntentPaymentOperations.as_view({"get": "list"}), name="stripe_payment_list"),
    path("confirmpayment", payment_views.IntentPaymentOperations.as_view({"put": "update"}), name="confirm payment"),
    path("cancelpayment", payment_views.CancelPaymentIntent.as_view({"post": "create"}), name="create cancel payment"),
    path("retrievepayment", payment_views.IntentPaymentOperations.as_view({"get": "retrieve"}), name="retrieve payment "
                                                                                                     "info"),
    path("modifypayment", payment_views.ModifyPaymentIntent.as_view({"put": "update"}), name="modify payment intent"),
    # Admin
    path("adminaccount", payment_views.AdminAccount.as_view({"post": "create"}), name="Admin account create"),
    path("bankaccount", payment_views.BankAccount.as_view({"post": "create", "get": "list"}), name="add bank account"),
    # InAppPurchase Android
    path("updatetokenandroid", payment_views.UpdatePurchaseTokenAndroid.as_view({"put": "update"}),
         name="purchase token android"),
    path("webhookandriod", payment_views.UpdateSubscriptionWebhookAndroid.as_view({"put": "update"}),
         name="subscription-webhook-android"),

]
