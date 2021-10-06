from abc import ABC, ABCMeta
from multiprocessing import Process

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

""" import models"""
from accounts.models import User, AccountVerification, ScheduleMeeting
from admins.models import TimeSlot

""" import serializer"""
from accounts.serializers import UserSerializer


class TimeSlotsSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        slot_obj = TimeSlot.objects.create(**validated_data)
        return slot_obj

    def update(self, instance, valiadated_data):
        TimeSlot.objects.filter(id=instance.id, is_deleted=False).update(**valiadated_data)
        return valiadated_data

    class Meta:
        model = TimeSlot
        fields = ('__all__')


class AdminSignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(min_length=5, max_length=50, required=True)
    password = serializers.CharField(min_length=8, max_length=20, required=True, write_only=True)

    @staticmethod
    def validate_email(email):
        if User.all_objects.filter(email=email.lower()).exists():
            raise serializers.ValidationError(validation_message.get("EMAIL_ALREADY_EXIST"))
        return email.lower()

    def create(self, validated_data):
        user_password = validated_data.pop('password')
        user_obj = User.objects.create(**validated_data)
        user_obj.set_password(user_password)
        user_obj.save()
        token = core_utils.get_or_create_user_token(user_obj)
        user_obj.is_admin_approved = True
        user_obj.is_email_verified = True
        user_obj.save()
        return user_obj

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'email', 'profile_image', 'company', 'address',
                  'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'password')


class ListUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'email', 'profile_image', 'company', 'address',
                  'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'is_active')


class UserSignUpByAdminSerializer(serializers.ModelSerializer):
    """
    Users signup serializer by Admin
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
        if User.all_objects.filter(email=email.lower()).exists():
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
        token = core_utils.get_or_create_user_token(user_obj)
        user_obj.is_admin_approved = True
        user_obj.is_email_verified = True
        user_obj.save()
        # Remove during production
        ##########################
        self.validated_data['token'] = token
        ##########################
        return user_obj

    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'email', 'company',
                  'address', 'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'password')


class ListMeetingsByStateSerializer(serializers.ModelSerializer):
    user = UserSerializer(fields=('id', 'email', 'full_name', 'first_name', 'last_name'))

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country",
                  # 'card_id', 'payment_intent_id'
                  )


class ListUpcomingMeetingsSerializer(serializers.ModelSerializer):
    user = UserSerializer(fields=('id', 'email', 'full_name', 'first_name', 'last_name'))

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country",
                  # 'card_id', 'payment_intent_id'
                  )


class ToggleUserStateSerializer(serializers.ModelSerializer):
    """
    serializer to inactive the user , activate the user and delete the user
    When deleting the user then , is_active=False and is_deleted=True is done
    """

    def update(self, instance, validated_data):
        user_id = self.context.get('user_id')
        is_deleted = self.context.get('is_deleted')
        is_active = self.context.get('is_active')
        if is_active:
            instance.is_active = is_active
        if is_deleted:
            instance.is_deleted = is_deleted
            instance.is_admin_approved = False
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'email', 'company', 'is_active', 'is_deleted',
                  'address', 'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified')


class UserRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'email', 'company', 'address', 'profile_image',
                  'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'is_active')


class MeetRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country",
                  # 'card_id', 'payment_intent_id'
                  )


class MeetingUpdateSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        meeting_id = self.context.get('meeting_id')
        if validated_data.get('amount') and instance.payment_via == ScheduleMeeting.SUBSCRIPTION:
            raise CustomException(status_code=400, message=validation_message.get("SUBSCRIPTION_AMOUNT_CHANGE"),
                                  location=validation_message.get("LOCATION"))
        obj = ScheduleMeeting.objects.filter(id=meeting_id)
        if validated_data.get('consultant_feedback'):
            cf = validated_data.get('consultant_feedback')
            core_utils.consultant_feedback_update_function(obj,cf)
        if validated_data.get('amount'):
            amount = validated_data.get('amount')
            core_utils.amount_update_function(obj, amount)
        if validated_data.get('admin_response'):
            admin_response = validated_data.get('admin_response')
            core_utils.admin_response_update_function(obj, admin_response)
        return instance

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country",
                  # 'card_id', 'payment_intent_id'
                  )


class ListRequestedMeetingsSerializer(serializers.ModelSerializer):
    user = UserSerializer(fields=('id', 'email', 'full_name', 'first_name', 'last_name'))

    class Meta:
        model = ScheduleMeeting
        fields = ('id', 'user', 'question_answer', 'compliance', 'time_slot', 'amount', 'meet_link',
                  'state', 'start_datetime', 'end_datetime', 'complaince_challenge', 'consultant_feedback',
                  'payment_via', 'admin_response', 'cancellation_charge', "region_country",
                  # 'card_id', 'payment_intent_id'
                  )

class ListUsersSignupRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'full_name', 'email', 'profile_image', 'company', 'address',
                  'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified', 'password')


class UserRequestsSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        user_id = self.context.get('user_id')
        is_admin_approved = self.context.get('is_admin_approved')
        is_deleted = self.context.get("is_deleted")
        if is_admin_approved:
            instance.is_admin_approved = True
            instance.save()
        if is_deleted == "True":
            # hard deleting the user as per guidelines
            User.objects.filter(id=user_id).delete()
        return instance

    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'email', 'company', 'is_active', 'is_deleted',
                  'address', 'phone_number', 'user_role', 'is_admin_approved', 'is_email_verified')
