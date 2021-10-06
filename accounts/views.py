""" rest framework import """
from django.db.models import Avg, Count, Sum, Q, Value, CharField, OuterRef, Exists, Subquery
from rest_framework import status as status_code
from rest_framework import mixins, views, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authtoken.models import Token
from rest_framework import viewsets, mixins, filters

''' project level import '''
from core.authentication import CustomTokenAuthentication
from core.exception import get_custom_error, CustomException
from core.messages import success_message, validation_message
from core.pagination import CustomPagination
from core.permissions import IsAdmin, IsUser
from core.response import SuccessResponse
from core import utils as core_utils
from config.local import emailverification_url
from multiprocessing import Process

""" model import """
from accounts.models import (User, AccountVerification, ScheduleMeeting, DeviceManagement, CountryRegion,
                             UserActivity)
from accounts.serializers import (UserSignUpSerializer, VerifyEmailSerializer, LoginSerializer,
                                  UserForgotPasswordSerializer, UserResetPasswordSerializer,
                                  ResendVerifyEmailSerializer,
                                  ScheduleMeetingsSerializer, ScheduleMeetingsRetrieveSerializer,
                                  ChangePasswordSerializer, UpdateUserProfileSerializer,
                                  VerifyEmailUserUpdateSerializer, CancelMeetingSerializer,
                                  ListRegionCountrySerializer, NotificationListSerializer)

import logging

log = logging.getLogger(__name__)


class UserSignUp(viewsets.ViewSet):
    """
    UserSignUpViewSet
        This class combines the logic of Craete operations for users.
        Inherits: BaseUserViewSet
    """
    permission_classes = (AllowAny,)
    serializer_class = UserSignUpSerializer

    def create(self, request):
        """
                post method used for the signup.
            :param request:
            :return: response
        """
        # log.info(request.data)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.save()
        serialize_data = serializer.data
        # Remove during production
        ##########################
        serialize_data.update({'email_verification_token': serializer.validated_data.get('email_verification_token'),
                               'token': serializer.validated_data.get('token')})
        ##########################
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)


class VerifyEmail(viewsets.ViewSet):
    """
        VerifyEmailAddress class used to verify user email.
    """
    permission_classes = (AllowAny,)
    serializer_class = VerifyEmailSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        bool_val = serializer.save()
        if bool_val:
            return SuccessResponse({"message": success_message.get('EMAIL_VERIFIED'), "res_status": 1},
                                   status=status_code.HTTP_200_OK)
        return SuccessResponse({"message": validation_message.get("WRONG_TOKEN"), "res_status": 2},
                               status=status_code.HTTP_200_OK)


class Login(viewsets.ViewSet):
    """
    user login viewset
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serialize_data = serializer.data
        serialize_data.pop('password')
        user = serializer.validated_data.get("user")
        if not user.is_admin_approved:
            return Response(get_custom_error(message="Kindly get the profile approved by Admin and then try to login.",
                                             error_location='Login', status=200),
                            status=status_code.HTTP_200_OK)
        if not user.is_email_verified:
            return Response(get_custom_error(message="Kindly get the email verified and then try to login.",
                                             error_location='Login', status=200),
                            status=status_code.HTTP_200_OK)
        # creating the obj of device from which it is logged in to send notification to admin
        fcm_token = request.data['fcm_token']
        DeviceManagement.objects.update_or_create(user=serializer.validated_data.get('user'),
                                                  # device_uuid=device_uuid,
                                                  defaults={
                                                      # "device_uuid": device_uuid,
                                                      "fcm_token": request.data['fcm_token']})
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)


class UserForgotPassword(viewsets.ViewSet):
    """
    Link will be sent to the mail for reseting the password
    """
    permission_classes = (AllowAny,)
    serializer_class = UserForgotPasswordSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Remove during production
        forgot_password_url = serializer.validated_data.get("forgot_password_url")
        # Remove during production forgot_password_url key
        return SuccessResponse({"message": success_message.get('FORGOT_PASSWORD_LINK_SUCCESS_MESSAGE'),
                                "forgot_password_url": forgot_password_url}, status=status_code.HTTP_200_OK)


class UserResetPassword(viewsets.ViewSet):
    """
    When the user click on forgot url on the email , then user reset password will be done
    """
    permission_classes = (AllowAny,)
    serializer_class = UserResetPasswordSerializer

    def create(self, request):
        """
            method used to call on Forgot Password.
        :param request:
        :return:
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        bool_val = serializer.save()
        if bool_val:
            return SuccessResponse({"message": success_message.get('PASSWORD_CHANGED'), "res_status": 1},
                                   status=status_code.HTTP_200_OK)
        return SuccessResponse({"message": validation_message.get("FORGOT_PASSWORD_LINK_ALREADY_VERIFIED"),
                                "res_status": 2},
                               status=status_code.HTTP_200_OK)


class ResendVerifyEmail(viewsets.ViewSet):
    """
    When the is_email_verified is false and user tries to login , then resend verification link button will be
    displayed so that verification link again goes to the email.
    """
    permission_classes = (AllowAny,)
    serializer_class = ResendVerifyEmailSerializer

    def create(self, request):
        email = request.query_params.get('email')
        serializer = self.serializer_class(data=request.data, context={'request': request.user, 'email': email})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse({"message": success_message.get('RESEND_EMAIL_VERIFY_LINK')},
                               status=status_code.HTTP_200_OK)


class ScheduleMeetings(viewsets.ViewSet):
    """
    scheduling the meeting by the user
    Note : There will be object created on "Proceed to Pay" click , and in response the object will be given,
    once the object is created then , update API will be hit for any further alterations in object .
    """
    permission_classes = (IsUser,)
    serializer_class = ScheduleMeetingsSerializer
    pagination_class = CustomPagination
    action_serializers = {
        'create': ScheduleMeetingsSerializer,
        'update': ScheduleMeetingsSerializer,
        'retrieve': ScheduleMeetingsRetrieveSerializer,
        'list': ScheduleMeetingsRetrieveSerializer,
    }

    def create(self, request):
        email = request.user.email
        serializer = self.serializer_class(data=request.data, context={'request': request, 'email': email})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)

    def update(self, request, meeting_id):
        instance = ScheduleMeeting.objects.filter(id=meeting_id).first()
        if not instance:
            return Response(get_custom_error(status=400, message=validation_message.get("MEET_ID_WRONG"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.action_serializers.get(self.action)(data=request.data, instance=instance,
                                                              context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)

    def retrieve(self, request, meeting_id):
        instance = ScheduleMeeting.objects.filter(id=meeting_id, is_deleted=False).first()
        if not instance:
            return Response(get_custom_error(status=400, message=validation_message.get("MEET_ID_WRONG"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.action_serializers.get(self.action)(instance)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)

    def list(self, request):
        page_size = request.GET.get('page_size', '')
        meet_state = request.query_params.get('meet_state')
        """
        All meeting = 1, Cancel = 2, Upcoming = 3, Completed = 4
        """
        if meet_state == "1":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=request.user
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "2":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=request.user,
                                                      state=ScheduleMeeting.CANCEL,
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "3":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=request.user,
                                                      state=ScheduleMeeting.PAYMENT_PROCESSED,
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "4":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=request.user,
                                                      state=ScheduleMeeting.COMPLETED,
                                                      ).select_related('user').all().order_by('-id')
        if page_size:
            pagination_class = self.pagination_class()
            page = pagination_class.paginate_queryset(instance, request)
            if page is not None:
                serializer = self.action_serializers.get(self.action)(page, many=True)
                return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data)
        serializer = self.action_serializers.get(self.action)(instance, many=True)
        return SuccessResponse(serializer.data)


class ChangePassword(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsUser,)
    serializer_class = ChangePasswordSerializer

    def update(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        response = {
            "message": success_message.get("PASSWORD_CHANGED"),
            "token": serializer.validated_data.get("token"),
        }
        return SuccessResponse(response, status=status_code.HTTP_200_OK)


class UpdateUserProfile(viewsets.ViewSet):
    permission_classes = (IsUser,)
    serializer_class = UpdateUserProfileSerializer

    def update(self, request, user_id):
        user_obj = User.objects.filter(id=user_id).first()
        serializer = self.serializer_class(
            instance=user_obj, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serialize_data = serializer.data
        # Remove during production
        serialize_data.update({'email_verification_token': serializer.validated_data.get('email_verification_token')})
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)


class VerifyEmailUserUpdate(viewsets.ViewSet):
    """
        VerifyEmailUserUpdate class used to verify user email when user updates his profile.
    """
    permission_classes = (AllowAny,)
    serializer_class = VerifyEmailUserUpdateSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        bool_val = serializer.save()
        if bool_val:
            return SuccessResponse({"message": success_message.get('EMAIL_VERIFIED'), "res_status": 1},
                                   status=status_code.HTTP_200_OK)
        return SuccessResponse({"message": validation_message.get("EMAIL_ALREADY_VERIFIED"), "res_status": 2},
                               status=status_code.HTTP_200_OK)


class CancelMeeting(viewsets.ViewSet):
    permission_classes = (IsUser,)
    serializer_class = CancelMeetingSerializer

    def update(self, request, meeting_id):
        meet_obj = ScheduleMeeting.objects.filter(id=meeting_id).first()
        if not meet_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("MEET_ID_WRONG"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(instance=meet_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse({"message": success_message.get("CANCEL_MEET")}, status=status_code.HTTP_200_OK)


class ListRegionCountry(viewsets.ViewSet, viewsets.GenericViewSet):
    permission_classes = (IsUser,)
    serializer_class = ListRegionCountrySerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ()

    def list(self, request):
        instance = CountryRegion.objects.filter().all().order_by('region')
        instance = self.filter_queryset(instance)
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(instance, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)


class IsEmailVerifiedResendLink(viewsets.ViewSet):

    def create(self, request):
        # create verification tken for email verification of user
        user_obj = User.objects.filter(email=request.query_params.get('email')).first()
        if not user_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("USER_NOT_FOUND"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        verification_token = core_utils.generate_verification_token(user_obj, AccountVerification.EMAIL_VERIFICATION)
        email_verification_url = emailverification_url + verification_token.token + "/"
        # send verificationtoken to email by threading process
        threading_process = Process(target=core_utils.send_verification_link_to_email,
                                    args=(user_obj.email, email_verification_url))
        threading_process.start()
        # remove in production
        return SuccessResponse({"message": success_message.get('EMAIL_SENT'),  # for verifying(is_email_verified).
                                "link": email_verification_url},  # comment this line in production
                               status=status_code.HTTP_200_OK)


class DeleteFCMToken(viewsets.ViewSet):
    permission_classes = (IsUser,)

    def destroy(self, request):
        obj = DeviceManagement.objects.filter(user_id=request.user).first()
        if obj:
            obj.delete()
        return Response("Fcm_token has been deleted")


class NotificationList(viewsets.ViewSet):
    permission_classes = (IsUser, )
    serializer_class = NotificationListSerializer
    pagination_class = CustomPagination

    def list(self, request):
        instance = UserActivity.objects.filter(receiver=request.user).all().order_by('-updated_at')
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(instance, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
