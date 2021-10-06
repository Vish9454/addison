"""
    file contains project level methods
"""
import os
import secrets
import base64
import json
import uuid
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
import sendgrid
from multiprocessing import Process
from django.db.models.functions import TruncMonth, TruncDate, TruncYear
from django.db.models import Q
from itertools import chain
from django.contrib.gis.geos import Point
from django.db.models import Count, Max, Sum, Q, ExpressionWrapper
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.authtoken.models import Token
from sendgrid.helpers.mail import Content, Email, Mail, To
from sendgrid import SendGridAPIClient
from config.local import (FROM_EMAIL, SEND_GRID_API_KEY, emailverification_url, FCM_SERVER_KEY)
from core.exception import CustomException
from core.messages import validation_message, success_message
from core.messages import variables
from rest_framework import serializers
from rest_framework.response import Response
from core.exception import get_custom_error, CustomException
from rest_framework import status as status_code
from pyfcm import FCMNotification
from django.core.mail import EmailMessage
from accounts.models import User, AccountVerification, ScheduleMeeting, UserActivity
from payments.models import InAppPurchase


def get_week_dates_mon_to_sunday(current_date):
    """
    current_date is in string
    """
    dt = datetime.strptime(current_date, variables.get('DATE_FORMAT'))
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_date_object_from_date(date):
    date_obj = datetime.strptime(date, "%d-%m-%Y")
    return date_obj


def get_date_object_from_date_updated(date):
    date_obj = datetime.strptime(date, variables.get("TIME_FORMAT"))
    return date_obj


def get_datetime_obj_format(date_time):
    datetime_obj = datetime.strptime(date_time, variables.get("DATETIME_FORMAT"))
    return datetime_obj


def get_current_date_time_object():
    """
        method used to get the current date time objects.
    :return: current_date_time_object
    """
    current_date_time_object = timezone.now()
    return current_date_time_object


def create_random_number():
    """
        method used to create random number.
    :return:
    """
    random_number = 1234  # secrets.choice(range(1000, 9999))
    return random_number


def save_user_coordinate(instance, latitude, longitude) -> object:
    """
        method used to save the user coordinates
    :param instance:
    :param latitude:
    :param longitude:
    :return:
    """
    point = Point(x=longitude, y=latitude, srid=4326)
    instance.coordinate = point
    return instance


def get_latitude_from_obj(instance):
    """
        method used to get the latitude of the address
    :param instance:
    :return:
    """
    try:
        latitude = instance.geo_point.y
    except Exception:
        latitude = 0
    return latitude


def get_longitude_from_obj(instance):
    """
        method used to get the longitude of the address
    :param instance:
    :return:
    """
    try:
        longitude = instance.geo_point.x
    except Exception:
        longitude = 0
    return longitude


def get_or_create_user_token(instance):
    """
        method used to create the user toke
    :param instance:
    :return: token key
    """
    token, created = Token.objects.get_or_create(user=instance)
    return token.key


def update_user_token(instance):
    """
        method used to create the user toke
    :param instance:
    :return: token key
    """
    """
    The function is written because when the email is updated then other device users have 
    to be logged out so for that the token gets changed and the token change code is rewritten below
    """
    user = Token.objects.filter(user=instance)
    t = Token.objects.get(user=User.objects.get(id=instance.id))
    user.update(key=t.generate_key())
    return user.first().key


# def update_or_create_fcm_detail(user, registration_id, device_type):
#     """
#         method used to save the fcm device token details
#     :param user:
#     :param device_type:
#     :param registration_id:
#     :return:
#     """
#     FCMDevice.objects.update_or_create(user=user, type=device_type, defaults={
#         "registration_id": registration_id,
#         "active": True
#     })
#     return True


def send_plain_mail_to_single_user(subject, email, message):
    """
            method used to send the token to email for email verification
        :param subject:
        :param email:
        :param message:
        :return:
        """
    email_body = message
    send_grid = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_KEY)
    from_email = Email(FROM_EMAIL)
    to_email = To(email)
    mail_subject = subject
    content = Content(variables.get("PLAIN_EMAIL_CONTENT_TYPE"), email_body)
    mail = Mail(from_email, to_email, mail_subject, content)
    try:
        send_grid.client.mail.send.post(request_body=mail.get())
    except Exception:
        print(validation_message.get("ERROR_IN_SENDING_MAIL"))
    return True


def send_plain_mail_to_multiple_user(subject, email_list, message):
    """
        method used to send the employee credentials to email.
        :param subject:
        :param email_list:
        :param message:
        :return:
        """
    email_body = message
    send_grid = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_KEY)
    from_email = Email(FROM_EMAIL)
    to_list = sendgrid.Personalization()
    for each in email_list:
        to_list.add_to(To(each))
    mail_subject = subject
    content = Content(variables.get("PLAIN_EMAIL_CONTENT_TYPE"), email_body)
    mail = Mail(from_email, None, mail_subject, content)
    mail.add_personalization(to_list)
    try:
        send_grid.client.mail.send.post(request_body=mail.get())
    except Exception:
        print(validation_message.get("ERROR_IN_SENDING_MAIL"))
    return True


def send_html_mail_to_single_user(subject, email, html_template, ctx_dict):
    """
        method used to send the employee credentials to email.
        :param subject:
        :param email:
        :param html_template:
        :param ctxt_dict:
        :return:
        """
    email_body = render_to_string(html_template, ctx_dict)
    send_grid = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_KEY)
    from_email = Email(FROM_EMAIL)
    to_email = To(email)
    mail_subject = subject
    content = Content(variables.get("HTML_EMAIL_CONTENT_TYPE"), email_body)
    mail = Mail(from_email, to_email, mail_subject, content)
    try:
        send_grid.client.mail.send.post(request_body=mail.get())
    except Exception:
        print(validation_message.get("ERROR_IN_SENDING_MAIL"))
    return True


def send_html_mail_to_multiple_user(subject, email_list, html_template, ctx_dict):
    """
        method used to send the restaurant employee credentials to email.
        :param subject:
        :param email_list:
        :param html_template:
        :param ctxt_dict:
        :return:
        """
    email_body = render_to_string(html_template, ctx_dict)
    send_grid = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_KEY)
    from_email = Email(FROM_EMAIL)
    to_list = sendgrid.Personalization()
    for each in email_list:
        to_list.add_to(To(each))
    mail_subject = subject
    content = Content(variables.get("HTML_EMAIL_CONTENT_TYPE"), email_body)
    mail = Mail(from_email, None, mail_subject, content)
    mail.add_personalization(to_list)
    try:
        send_grid.client.mail.send.post(request_body=mail.get())
    except Exception:
        print(validation_message.get("ERROR_IN_SENDING_MAIL"))
    return True


def check_file_size(file_obj):
    try:
        file_obj_size = file_obj.size
        file_in_mb = file_obj_size / 1000000
        if file_in_mb <= 5:
            return True
        return False
    except Exception:
        return False


def send_notification(user_device_obj, title, message, data):
    push_service = FCMNotification(api_key=FCM_SERVER_KEY)
    fcm_token = []
    for token in user_device_obj:
        fcm_token.append(token.fcm_token)
    print(push_service.notify_multiple_devices(registration_ids=fcm_token, message_title=title,
                                               message_body=message, data_message=data))
    return push_service.notify_multiple_devices(registration_ids=fcm_token, message_title=title,
                                                message_body=message, data_message=data)


def send_verification_link_to_email(email, verification_link):
    """
        method used to send email verification link to email.
    :param email:
    :param verification_link:
    :return:
    """
    subject = 'Email Verification'
    html_template = 'verify_mail.html'
    ctx_dict = {'email': email, 'verification_link': verification_link}
    send_html_mail_to_single_user(subject, email, html_template, ctx_dict)


def send_forgot_password_link_to_email(email, forgot_password_link):
    """
        method used to send forgot password link to email.
    :param email:
    :param forgot_password_link:
    :return:
    """
    subject = 'Forgot Password'
    html_template = 'forgot_password.html'
    ctx_dict = {'email': email, 'forgot_password_link': forgot_password_link}
    send_html_mail_to_single_user(subject, email, html_template, ctx_dict)


def resend_email_verify_link(instance):
    """
        method used to send forgot password link to email.
    :param instance:
    :return:
    """
    verification_token = generate_verification_token(instance, AccountVerification.VerificationType.
                                                     EMAIL_VERIFICATION)
    email_verification_url = emailverification_url + verification_token.token + "/"
    # send verification token to email
    p = Process(target=send_verification_link_to_email,
                args=(instance.email, email_verification_url,))
    p.start()
    return True


def generate_verification_token(instance, verification_type):
    """
        method used to generate the verification type
    :param instance:
    :param verification_type:
    :return:
    """
    # create random number of 6 digit
    token = uuid.uuid4().hex
    user_token = AccountVerification.objects.filter(user=instance.id,
                                                    verification_type=verification_type).only('id').first()
    if user_token:
        user_token.delete()
    token_expired_at = timezone.now() + timedelta(hours=variables.get('OTP_EXPIRATION_TIME'))
    user_token = AccountVerification.objects.create(token=token, verification_type=verification_type,
                                                    user=instance, expired_at=token_expired_at)
    return user_token


def group_sum(key, list_of_dicts):
    d = {}
    for dct in list_of_dicts:
        if dct[key] not in d:
            d[dct[key]] = {}
        for k, v in dct.items():
            if k != key:
                if k not in d[dct[key]]:
                    d[dct[key]][k] = v
                else:
                    d[dct[key]][k] += v
    final_list = []
    for k, v in d.items():
        temp_d = {key: k}
        for k2, v2 in v.items():
            temp_d[k2] = v2
        final_list.append(temp_d)
    return final_list


def get_year_wise_earnings(all_meeting):
    """
    By default year wise earnings will be displayed
    """
    completed_meeting_earning = all_meeting.filter(state=4).annotate(year=TruncYear('start_datetime')
                                                                     ).values('year').annotate(sum=Sum('amount'))

    cancelled_meeting_earning = all_meeting.filter(state=2).annotate(year=TruncYear('start_datetime')
                                                                     ).values('year').annotate(
        sum=Sum('cancellation_charge'))
    combined_data = list(chain(completed_meeting_earning, cancelled_meeting_earning))
    grouped_data = group_sum("year", combined_data)
    return grouped_data


def get_monthly_wise_earning(all_meeting, year):
    """
    if year is selected then in that year all the 12 months earnings will be shown
    """
    completed_meeting_earning = all_meeting.filter(state=4, start_datetime__year=year,
                                                   ).annotate(month=TruncMonth('start_datetime')
                                                              ).values('month').annotate(sum=Sum('amount'))

    cancelled_meeting_earning = all_meeting.filter(state=2, start_datetime__year=year,
                                                   ).annotate(month=TruncMonth('start_datetime')
                                                              ).values('month').annotate(
        sum=Sum('cancellation_charge'))
    combined_data = list(chain(completed_meeting_earning, cancelled_meeting_earning))
    grouped_data = group_sum("month", combined_data)
    return grouped_data


def get_daily_for_month_earnings(all_meeting, year, month):
    """
    if year and then month is selected then in that month all the earnings will be displayed for each date
    """
    completed_meeting_earning = all_meeting.filter(state=4, start_datetime__year=year, start_datetime__month=month
                                                   ).annotate(date=TruncDate('start_datetime')
                                                              ).values('date').annotate(sum=Sum('amount'))

    cancelled_meeting_earning = all_meeting.filter(state=2, start_datetime__year=year, start_datetime__month=month
                                                   ).annotate(date=TruncDate('start_datetime')
                                                              ).values('date').annotate(sum=Sum('cancellation_charge'))
    combined_data = list(chain(completed_meeting_earning, cancelled_meeting_earning))
    grouped_data = group_sum("date", combined_data)
    return grouped_data


def get_specific_dates_earnings(all_meeting, start_date, end_date):
    """
    if year and then month and then start and end date is selected then all the earnings
    will be displayed for between start and end date.
    """
    completed_meeting_earning = all_meeting.filter(state=4, start_datetime__date__gte=start_date,
                                                   start_datetime__date__lte=end_date
                                                   ).annotate(day=TruncDate('start_datetime')
                                                              ).values('day').annotate(sum=Sum('amount'))

    cancelled_meeting_earning = all_meeting.filter(state=2, start_datetime__date__gte=start_date,
                                                   start_datetime__date__lte=end_date
                                                   ).annotate(day=TruncDate('start_datetime')
                                                              ).values('day').annotate(sum=Sum('cancellation_charge'))
    combined_data = list(chain(completed_meeting_earning, cancelled_meeting_earning))
    grouped_data = group_sum("day", combined_data)
    return grouped_data


def create_exception_message(ex):
    if hasattr(ex, 'user_message'):
        msg = ex.user_message
    else:
        msg = "Something went wrong please try again later."
    return msg


def consultant_feedback_update_function(obj, cf):
    obj.update(consultant_feedback=cf)
    title = "Kindly check the notification"
    message = "Meeting details have been updated"
    data = {"consultant_feedback": obj.first().consultant_feedback}
    noti_obj = User.objects.filter(user_role=1).first()
    filtered_obj = noti_obj.user_device.filter(is_active=True).all()
    UserActivity.objects.create(sender_id=noti_obj.id, receiver_id=obj.first().user_id,
                                activity_type=UserActivity.ADMIN_SEND_YOU_A_NOTIFICATION__FOR_FEEDBACK,
                                title=title, message=message, payload=data)
    # core_utils.send_notification(user_device_obj=filtered_obj,
    #                              title=title,
    #                              message=message,
    #                              data=data)


def amount_update_function(obj, amount):
    obj.update(amount=amount)
    title = "Kindly check the notification"
    message = "Meeting details have been updated"
    data = {"amount": obj.first().amount}
    noti_obj = User.objects.filter(user_role=1).first()
    filtered_obj = noti_obj.user_device.filter(is_active=True).all()
    UserActivity.objects.create(sender_id=noti_obj.id, receiver_id=obj.first().user_id,
                                activity_type=UserActivity.ADMIN_SEND_YOU_A_NOTIFICATION__FOR_FEEDBACK,
                                title=title, message=message, payload=data)
    # core_utils.send_notification(user_device_obj=filtered_obj,
    #                              title=title,
    #                              message=message,
    #                              data=data)


def admin_response_update_function(obj, admin_response):
    obj.update(admin_response=admin_response)
    title = "Kindly check the notification"
    message = "Meeting details have been updated"
    noti_obj = User.objects.filter(user_role=1).first()
    filtered_obj = noti_obj.user_device.filter(is_active=True).all()
    # print(admin_response)
    if admin_response == ScheduleMeeting.ACCEPT_ADMIN:
        data = {"admin_response": "Admin accepted the meeting."}
        UserActivity.objects.create(sender_id=noti_obj.id, receiver_id=obj.first().user_id,
                                    activity_type=UserActivity.ADMIN_SEND_YOU_A_NOTIFICATION_ACCEPT_MEETING,
                                    title=title, message=message, payload=data)
    if admin_response == ScheduleMeeting.RESCHEDULE_ADMIN:
        data = {"admin_response": "Admin has rescheduled the meeting, kindly check the meeting details."}
        UserActivity.objects.create(sender_id=noti_obj.id, receiver_id=obj.first().user_id,
                                    activity_type=UserActivity.ADMIN_SEND_YOU_A_NOTIFICATION_RESCHEDULE_MEETING,
                                    title=title, message=message, payload=data)
    if admin_response == ScheduleMeeting.REJECT_ADMIN:
        data = {"admin_response": "Admin has cancelled the meeting, sorry for the inconvience"}
        UserActivity.objects.create(sender_id=noti_obj.id, receiver_id=obj.first().user_id,
                                    activity_type=UserActivity.ADMIN_SEND_YOU_A_NOTIFICATION_REJECT_MEETING,
                                    title=title, message=message, payload=data)
        # cancelling the meeting, after this the api for refunding amount will be executed if payment on hold
        # method is used
        obj.update(state=2)
    # core_utils.send_notification(user_device_obj=filtered_obj,
    #                              title=title,
    #                              message=message,
    #                              data=data)


def payment_on_android(data):
    """
    method used to authenticate payment through the google.
    """
    try:
        import ast
        decoded_data = base64.b64decode(data)
        decoded_data = decoded_data.decode('UTF-8')
        decoded_data = json.loads(decoded_data)
        subscription_obj = decoded_data["subscriptionNotification"]
        purchase_token = subscription_obj["purchaseToken"]
        notification_type = subscription_obj["notificationType"]
        # Fetch all user objects that have this purchase token(Many to one
        # relationship as there might be a case that same subscription being used by different users)
        queryset = User.objects.filter(purchase_token=purchase_token).all()
        if queryset:
            if notification_type == 3:
                """for renewal"""
                for obj in queryset:
                    obj.subscription_end = obj.subscription_end + relativedelta(months=int(obj.interval))
                    obj.save()
            elif notification_type == 13 or notification_type == 3:
                """for expiry=13"""
                """for cancelling subscription=3"""
                for obj in queryset:
                    obj.subscription_end = datetime.now()
                    obj.is_subscribed = False
        else:
            return Response(get_custom_error(message=validation_message.get('INVALID_PURCHASE_TOKEN'),
                                             error_location='webhook', status=400),
                            status=status_code.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(get_custom_error(message=validation_message.get('ERROR'),
                                         error_location='webhook', status=400),
                        status=status_code.HTTP_400_BAD_REQUEST)
    return True
