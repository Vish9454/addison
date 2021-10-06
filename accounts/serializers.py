from abc import ABC, ABCMeta
from multiprocessing import Process
from datetime import date, datetime, timedelta, time, timezone

''' project level imports '''
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers, fields
from rest_framework.authtoken.models import Token
from config.local import forgotpassword_url, emailverification_url
from core import utils as core_utils
from core.exception import CustomException
from core.messages import validation_message, variables
from core import serializers as core_serializers
from django.contrib.gis.db import models
from core.serializers import DynamicFieldsModelSerializer

""" model import """
from accounts.models import (User, AccountVerification, ScheduleMeeting, DeviceManagement, CountryRegion,
                             UserActivity)
from admins.models import TimeSlot


class UserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'email', 'company', 'address', 'profile_image',
                  'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'password')


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    Users signup serializer
    """
    email = serializers.EmailField(min_length=5, max_length=50, required=True)
    password = serializers.CharField(min_length=8, max_length=20, required=True, write_only=True)

    @staticmethod
    def validate_email(email):
        """
            method used to check email already exits in users table or not.
        :param email:
        :return:
        """
        if User.all_delete_objects.filter(email=email.lower()).exists():
            raise serializers.ValidationError(validation_message.get("EMAIL_ALREADY_EXIST"))
        return email.lower()

    def create(self, validated_data):
        """
                    method used to create the data.
                :param validated_data:
                :return:
                """
        # create user object
        user_password = validated_data.pop('password')
        user_obj = User.objects.create(**validated_data)
        user_obj.set_password(user_password)
        user_obj.save()
        # create verification tken for email verification of user
        verification_token = core_utils.generate_verification_token(user_obj, AccountVerification.EMAIL_VERIFICATION)
        email_verification_url = emailverification_url + verification_token.token + "/"
        # send verificationtoken to email by threading process
        threading_process = Process(target=core_utils.send_verification_link_to_email,
                                    args=(user_obj.email, email_verification_url))
        threading_process.start()
        token = core_utils.get_or_create_user_token(user_obj)
        # Remove during production
        ##########################
        self.validated_data['email_verification_token'] = email_verification_url
        self.validated_data['token'] = token
        # user_obj.is_admin_approved = True
        # user_obj.is_email_verified = True
        user_obj.save()
        ##########################
        return user_obj

    class Meta:
        model = User
        fields = (
        'id', 'full_name', 'first_name', 'last_name', 'email', 'company', 'address', 'phone_number', 'user_role',
        'is_admin_approved', 'is_email_verified', 'password')


class VerifyEmailSerializer(serializers.Serializer):
    """
    verify the email serializer
    """
    otp = serializers.CharField(required=True)

    def create(self, validated_data):
        request = self.context.get('request')
        account_verify = AccountVerification.objects.select_related('user').filter(
            token=validated_data.get('otp'),
            verification_type=AccountVerification.EMAIL_VERIFICATION).only('expired_at', 'is_used', 'user').first()
        if not account_verify:
            return False
        account_verify.user.is_email_verified = True
        account_verify.is_used = True
        account_verify.save()
        account_verify.user.save()
        user_id = account_verify.user_id
        return True


class LoginSerializer(serializers.ModelSerializer):
    """
    login of user serializer
    """
    ADMIN = 1
    USER = 2
    ROLE = (
        (ADMIN, "Admin"),
        (USER, "User"),
    )
    user_role = serializers.ChoiceField(choices=ROLE)
    email = serializers.EmailField(min_length=5, max_length=50, required=True)
    password = serializers.CharField(min_length=8, max_length=20, required=True)

    def validate(self, attrs):
        user_obj = User.objects.filter(email=attrs["email"].lower()).first()
        if user_obj:
            if user_obj.user_role != attrs["user_role"]:
                raise CustomException(status_code=403, message=validation_message.get("INVALID_USER_ROLE"),
                                      location=validation_message.get("LOCATION"))
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if user is not None:
            attrs["user"] = user
        else:
            raise serializers.ValidationError(validation_message.get('INVALID_CREDENTIAL'))
        return attrs

    def create(self, validated_data):
        user_obj = User.objects.filter(email=validated_data.get('email')).first()
        return user_obj

    def to_representation(self, instance):
        data = super(LoginSerializer, self).to_representation(instance)
        data['token'] = core_utils.get_or_create_user_token(instance)
        return data

    class Meta:
        model = User
        fields = (
        'id', "email", "password", "user_role", 'full_name', 'first_name', 'last_name', 'phone_number', 'profile_image',
        'company', 'address', 'user_role', 'is_email_verified', 'is_admin_approved')


class UserForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=5, max_length=50, required=True)

    def create(self, validated_data):
        instance = User.objects.filter(email=validated_data.get('email').lower()).only('id', 'email', ).first()
        if not instance:
            raise CustomException(status_code=400, message=validation_message.get("USER_NOT_FOUND"),
                                  location=validation_message.get("LOCATION"))
        # create the forgot password token
        forgot_password_token = core_utils.generate_verification_token(instance, AccountVerification.FORGOT_PASSWORD)
        forgot_password_url = forgotpassword_url + forgot_password_token.token + "/"
        # send forgot password token to email
        p = Process(target=core_utils.send_forgot_password_link_to_email,
                    args=(instance.email, forgot_password_url,))
        p.start()
        # Remove during production
        self.validated_data["forgot_password_url"] = forgot_password_url
        return True


class UserResetPasswordSerializer(serializers.Serializer):
    """method to reset user's password"""

    token = serializers.CharField(required=True)
    password = serializers.CharField(min_length=8, max_length=20, required=True)

    @staticmethod
    def get_account_verification_detail(forgot_password_token):
        account_verify = AccountVerification.objects.select_related('user'). \
            filter(token=forgot_password_token, verification_type=AccountVerification.
                   FORGOT_PASSWORD).only('expired_at', 'is_used', 'user').first()
        if not account_verify:
            raise CustomException(status_code=400, message=validation_message.get("INVALID_FORGOT_PASSWORD_LINK"),
                                  location=validation_message.get("LOCATION"))
        return account_verify

    def create(self, validated_data):
        """
            method used to create the data.
        :param validated_data:
        :return:
        """
        account_verify = self.get_account_verification_detail(validated_data['token'])
        if account_verify.is_used:
            return False
        # To check expiration time of link
        if account_verify.expired_at < core_utils.get_current_date_time_object():
            raise CustomException(status_code=400, message=validation_message.get("RESET_PASSWORD_LINK_EXPIRED"),
                                  location=validation_message.get("LOCATION"))
        user_obj = account_verify.user
        user_obj.set_password(validated_data["password"])
        user_obj.save()
        # deleting token to signout user out of other device
        Token.objects.filter(user=user_obj).delete()
        Token.objects.get_or_create(user=user_obj)

        # To mark token as used
        account_verify.is_used = True
        account_verify.save()
        return True


class ResendVerifyEmailSerializer(serializers.Serializer):
    """
        ResendEmailVerifyLinkSerializer used to resend email verification link.
    """

    def create(self, validated_data):
        """
            method used to create the data.
        :param validated_data:
        :return:
        """
        # create the email verification token
        email = self.context.get('email')
        instance = User.objects.filter(email=email.lower()).first()
        if not instance:
            raise CustomException(status_code=400, message=validation_message.get("USER_NOT_FOUND"),
                                  location=validation_message.get("LOCATION"))
        verification_token = core_utils.generate_verification_token(instance, AccountVerification.EMAIL_VERIFICATION)
        email_verification_url = emailverification_url + "?otp=" + verification_token.token + "&email=" + email
        # send verification token to email
        p = Process(target=core_utils.send_verification_link_to_email,
                    args=(email, email_verification_url,))
        p.start()
        return True


class ScheduleMeetingsSerializer(serializers.ModelSerializer):
    """
    meeting by user serializer
    Note : There will be object created on "Proceed to Pay" click , and in response the object will be given,
    once the object is created then , update API will be hit for any further alterations in object .
    """

    def create(self, validated_data):
        email = self.context.get('email')
        request = self.context.get('request')
        instance = User.objects.filter(email=email.lower()).first()
        if not instance:
            raise CustomException(status_code=400, message=validation_message.get("USER_NOT_FOUND"),
                                  location=validation_message.get("LOCATION"))
        meet_obj = ScheduleMeeting.objects.create(**validated_data, user=instance)
        time_slot_obj = TimeSlot.objects.filter(id=request.data.get('time_slot'), is_deleted=False).first()
        meet_obj.amount = time_slot_obj.amount
        meet_obj.end_datetime = core_utils.get_datetime_obj_format(request.data.get('start_datetime')
                                                                   ) + time_slot_obj.slots
        meet_obj.save()
        return meet_obj

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if validated_data.get('timeslot'):
            time_slot_obj = TimeSlot.objects.filter(id=request.data.get('time_slot'), is_deleted=False).first()
            instance.amount = instance.amount
            instance.end_datetime = core_utils.get_datetime_obj_format(request.data.get('start_datetime')
                                                                       ) + time_slot_obj.slots
            instance.save()
        ScheduleMeeting.objects.filter(id=instance.id).update(**validated_data)
        return_obj = ScheduleMeeting.objects.filter(id=instance.id).first()
        return return_obj

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', 'region_country',
                  # 'card_id', 'payment_intent_id'
                  )


class ScheduleMeetingsRetrieveSerializer(DynamicFieldsModelSerializer):
    user = UserSerializer(fields=('id', 'email', 'full_name', 'first_name', 'last_name'))

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country"
                  # 'card_id', 'payment_intent_id'
                  )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True, write_only=True, min_length=8, max_length=20
    )
    new_password = serializers.CharField(
        required=True, write_only=True, min_length=8, max_length=20
    )

    def validate(self, attrs):
        """to validate attributes"""
        request = self.context.get("request")
        user_obj = authenticate(
            email=request.user.email.lower(), password=attrs.get("old_password")
        )
        if not user_obj:
            raise serializers.ValidationError(validation_message.get('OLD_PASSWORD_WRONG'))
        user_obj.set_password(attrs["new_password"])
        user_obj.save()

        # deleting token to signout user out of other device
        Token.objects.filter(user=user_obj).delete()
        token, created = Token.objects.get_or_create(user=user_obj)
        attrs["token"] = token.key
        return attrs


class UpdateUserProfileSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        request = self.context.get('request')
        try:
            if User.all_objects.filter(email=request.data.get('email').lower()).exists():
                raise serializers.ValidationError(validation_message.get("EMAIL_ALREADY_EXIST"))
        except Exception:
            pass
        return attrs

    def update(self, instance, validated_data):
        request = self.context.get('request')
        data = User.objects.filter(id=instance.id)
        email = request.data.pop('email')
        email1 = validated_data.pop('email')
        if instance.email == email:
            pass
        else:
            # create the email verification token
            email = email.lower()
            verification_token = core_utils.generate_verification_token(request.user,
                                                                        AccountVerification.EMAIL_VERIFICATION)
            email_verification_url = emailverification_url + "?otp=" + verification_token.token + "&email=" \
                                     + email
            # send verification token to email
            p = Process(target=core_utils.send_verification_link_to_email,
                        args=(email, email_verification_url,))
            p.start()
            # Remove during production
            self.validated_data['email_verification_token'] = email_verification_url
            # here we are updating the key
            core_utils.update_user_token(instance)
        data.update(**validated_data)
        return_obj = User.objects.filter(id=instance.id).first()
        return return_obj

    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'profile_image',
                  'email', 'company', 'address', 'phone_number')


class VerifyEmailUserUpdateSerializer(serializers.Serializer):
    """
         VerifyEmailSerializer used to verify the email address when user updates his profile.
     """
    otp = serializers.CharField(required=True)

    def create(self, validated_data):
        request = self.context.get('request')
        account_verify = AccountVerification.objects.select_related('user'). \
            filter(token=validated_data.get('otp'), verification_type=AccountVerification.
                   EMAIL_VERIFICATION).only('expired_at', 'is_used', 'user').first()
        if not account_verify:
            raise CustomException(status_code=400, message=validation_message.get("INVALID_EMAIL_VERIFY_LINK"),
                                  location=validation_message.get("LOCATION"))
        if account_verify.is_used:
            return False
        account_verify.is_used = True
        account_verify.save()
        account_verify.user.save()
        user_id = account_verify.user_id
        User.objects.filter(id=user_id).update(email=request.data.get('email').lower())
        return True


class CancelMeetingSerializer(serializers.Serializer):

    def update(self, instance, validated_data):
        if instance.start_datetime - datetime.now(timezone.utc) < timedelta(hours=3):
            # cancellation_charge is in dollars
            instance.cancellation_charge = 20
        instance.state = ScheduleMeeting.CANCEL
        instance.save()
        return instance


class ListRegionCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryRegion
        fields = ('id', 'region', 'country')


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ('id', 'created_at', 'updated_at', 'sender', 'receiver', 'activity_type', 'title', 'message',
                  'payload', 'is_read')
