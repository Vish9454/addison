''' rest framework import '''
from django.db.models import Avg, Count, Sum, Q, Value, CharField, OuterRef, Exists, Subquery

from rest_framework import status as status_code
from rest_framework import mixins, views, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authtoken.models import Token
from datetime import date, datetime, timedelta, time, timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters

''' project level import '''
from core.authentication import CustomTokenAuthentication
from core.exception import get_custom_error, CustomException
from core.messages import success_message, validation_message, variables
from core.pagination import CustomPagination
from core.permissions import IsAdmin, IsUser
from core.response import SuccessResponse
from core import utils as core_utils

""" model import """
from admins.models import TimeSlot
from accounts.models import User, ScheduleMeeting

""" import serializers """
from admins.serializers import (TimeSlotsSerializer, AdminSignUpSerializer, ListUsersSerializer,
                                UserSignUpByAdminSerializer, ListMeetingsByStateSerializer,
                                ListUpcomingMeetingsSerializer, ToggleUserStateSerializer,
                                UserRetrieveSerializer, MeetRetrieveSerializer,
                                MeetingUpdateSerializer, ListRequestedMeetingsSerializer,
                                ListUsersSignupRequestSerializer, UserRequestsSerializer)


class TimeSlots(viewsets.ViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = TimeSlotsSerializer
    action_serializers = {
        'create': TimeSlotsSerializer,
        'retrieve': TimeSlotsSerializer,
        'list': TimeSlotsSerializer,
        'update': TimeSlotsSerializer,
    }

    def create(self, request):
        user_obj = User.objects.filter(id=request.user.id).first()
        if not user_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("USER_NOT_FOUND"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.action_serializers.get(self.action)(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serialize_data = serializer.data
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)

    def retrieve(self, request, timeslot_id):
        timeslot_obj = TimeSlot.objects.filter(id=timeslot_id, is_deleted=False).first()
        if timeslot_obj:
            serializer = self.action_serializers.get(self.action)(timeslot_obj)
            return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
        return SuccessResponse({}, status=status_code.HTTP_200_OK)

    def list(self, request):
        timeslot_obj = TimeSlot.objects.filter(is_deleted=False).all()
        if timeslot_obj:
            serializer = self.action_serializers.get(self.action)(timeslot_obj, many=True)
            return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
        return SuccessResponse({}, status=status_code.HTTP_200_OK)

    def update(self, request, timeslot_id):
        if request.data.get('slots'):
            return Response(get_custom_error(status=400, message=validation_message.get("DONT_UPDATE_SLOTS"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        timeslot_obj = TimeSlot.objects.filter(id=timeslot_id, is_deleted=False).first()
        if not timeslot_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("INVALID_SLOTS"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.action_serializers.get(self.action)(data=request.data, instance=timeslot_obj)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse({"message": success_message.get("UPDATE_SUCCESSFUL")}, status=status_code.HTTP_200_OK)


class AdminSignUp(viewsets.ViewSet):
    """
    UserSignUpViewSet
        This class combines the logic of Craete operations for users.
        Inherits: BaseUserViewSet
    """
    permission_classes = (AllowAny,)
    serializer_class = AdminSignUpSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.save()
        serialize_data = serializer.data
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)


class DashboardCountings(viewsets.ViewSet):
    permission_classes = (IsAdmin,)

    def list(self, request):
        current_date = request.query_params.get('current_date')
        start_date, end_date = core_utils.get_week_dates_mon_to_sunday(current_date)

        total_users_count = User.objects.filter(user_role=User.USER, is_deleted=False).all().count()

        all_meeting = ScheduleMeeting.objects.filter()

        completed_meeting_count = all_meeting.filter(state=4).all().count()
        completed_meeting_earning = all_meeting.filter(state=4).aggregate(Sum('amount'))
        cancelled_meeting_earning = all_meeting.filter(state=2).aggregate(Sum('cancellation_charge'))
        if completed_meeting_earning['amount__sum'] is None:
            completed_meeting_earning['amount__sum'] = 0
        if cancelled_meeting_earning['cancellation_charge__sum'] is None:
            cancelled_meeting_earning['cancellation_charge__sum'] = 0
        total_earning = completed_meeting_earning['amount__sum'] + cancelled_meeting_earning['cancellation_charge__sum']

        meeting_this_week_count = all_meeting.filter(start_datetime__gte=start_date,
                                                     end_datetime__lte=end_date).count()

        return SuccessResponse({"total_completed_meeting": completed_meeting_count,
                                "total_earning": total_earning,
                                "meeting_this_week": meeting_this_week_count,
                                "total_user_count": total_users_count}, status=status_code.HTTP_200_OK)


class DashboardGraph(viewsets.ViewSet):
    permission_classes = (IsAdmin,)

    def list(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        current_date = request.query_params.get('current_date')
        all_meeting = ScheduleMeeting.objects.filter()
        if year and not (month or start_date or end_date):
            meeting_earning = core_utils.get_monthly_wise_earning(all_meeting, year)
            return SuccessResponse(meeting_earning, status=status_code.HTTP_200_OK)
        if month and year and not (start_date and end_date):
            meeting_earning = core_utils.get_daily_for_month_earnings(all_meeting, year, month)
            return SuccessResponse(meeting_earning, status=status_code.HTTP_200_OK)
        if start_date and end_date:
            meeting_earning = core_utils.get_specific_dates_earnings(all_meeting, start_date, end_date)
            return SuccessResponse(meeting_earning, status=status_code.HTTP_200_OK)
        else:
            meeting_earning = core_utils.get_year_wise_earnings(all_meeting)
            return SuccessResponse(meeting_earning, status=status_code.HTTP_200_OK)


class ListUsers(viewsets.ViewSet, viewsets.GenericViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = ListUsersSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('email', 'full_name', 'address', 'phone_number')

    def list(self, request):
        # here is_active=False users will also be displayed
        user_obj = User.all_objects.filter(is_admin_approved=True).all().order_by('-id')
        user_obj = self.filter_queryset(user_obj)
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(user_obj, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(user_obj, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)


class UserSignUpByAdmin(viewsets.ViewSet):
    """
    UserSignUpByAdmin
        This class combines the logic of Craete operations for users by admin.
        Inherits: BaseUserViewSet
    """
    permission_classes = (AllowAny,)
    serializer_class = UserSignUpByAdminSerializer

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
        serialize_data.update({'token': serializer.validated_data.get('token')})
        ##########################
        return SuccessResponse(serialize_data, status=status_code.HTTP_200_OK)


class ListMeetingsByState(viewsets.ViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = ListMeetingsByStateSerializer
    pagination_class = CustomPagination

    def list(self, request):
        page_size = request.GET.get('page_size', '')
        meet_state = request.query_params.get('meet_state')
        user_id = request.query_params.get('user_id')
        """
        All meeting = 1, Cancel = 2, Upcoming = 3, Completed = 4
        """
        if meet_state == "1":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=user_id
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "2":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=user_id,
                                                      state=ScheduleMeeting.CANCEL,
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "3":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=user_id,
                                                      state=ScheduleMeeting.PAYMENT_PROCESSED,
                                                      ).select_related('user').all().order_by('-id')
        elif meet_state == "4":
            instance = ScheduleMeeting.objects.filter(is_deleted=False, user=user_id,
                                                      state=ScheduleMeeting.COMPLETED,
                                                      ).select_related('user').all().order_by('-id')
        if page_size:
            pagination_class = self.pagination_class()
            page = pagination_class.paginate_queryset(instance, request)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data)


class ListUpcomingMeetings(viewsets.ViewSet, viewsets.GenericViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = ListUpcomingMeetingsSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('start_datetime__date',)

    def list(self, request):
        challenge = request.GET.get('challenge')  # category of the challenge i.e complaince
        resheduled = request.query_params.get('resheduled')  # if rescheduled then pass 1
        instance = ScheduleMeeting.objects.filter(is_deleted=False, state=3
                                                  ).select_related('user').all().order_by('-id')
        if challenge:
            instance = instance.filter(compliance__in=eval(challenge)).all()
        if resheduled == "1":
            instance = instance.filter(admin_response=ScheduleMeeting.RESCHEDULE_ADMIN).all()
        instance = self.filter_queryset(instance)
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(instance, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)


class ToggleUserState(viewsets.ViewSet):
    """
    View to inactive the user , activate the user and delete the user
    """
    permission_classes = (IsAdmin,)
    serializer_class = ToggleUserStateSerializer

    def update(self, request):
        user_id = request.query_params.get('user_id')
        is_active = request.query_params.get('is_active')
        is_deleted = request.query_params.get('is_deleted')
        user_obj = User.all_objects.filter(id=user_id).first()
        if not user_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("USER_NOT_FOUND"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(
            instance=user_obj, data=request.data, partial=True, context={"request": request,
                                                                         "user_id": user_id,
                                                                         "is_active": is_active,
                                                                         "is_deleted": is_deleted}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if is_active == 'True':
            return SuccessResponse({"message": success_message.get('USER_ACTIVATED'),
                                }, status=status_code.HTTP_200_OK)
        if is_active == 'False':
            return SuccessResponse({"message": success_message.get('USER_DEACTIVATED'),
                                    }, status=status_code.HTTP_200_OK)
        if is_deleted == 'True':
            return SuccessResponse({"message": success_message.get('USER_DELETED'),
                                    }, status=status_code.HTTP_200_OK)



class UserRetrieve(viewsets.ViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = UserRetrieveSerializer

    def retrieve(self, request, user_id):
        user_obj = User.objects.filter(id=user_id).first()
        if user_obj:
            serializer = self.serializer_class(user_obj)
            return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
        return SuccessResponse({}, status=status_code.HTTP_200_OK)


class MeetRetrieve(viewsets.ViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = MeetRetrieveSerializer

    def retrieve(self, request, meet_id):
        meet_obj = ScheduleMeeting.objects.filter(id=meet_id).first()
        if meet_obj:
            serializer = self.serializer_class(meet_obj)
            return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)
        return SuccessResponse({}, status=status_code.HTTP_200_OK)


class MeetingUpdate(viewsets.ViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = MeetingUpdateSerializer

    def update(self, request, meeting_id):
        meet_obj = ScheduleMeeting.objects.filter(id=meeting_id).first()
        if not meet_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("MEET_ID_WRONG"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(instance=meet_obj, data=request.data, partial=True,
                                           context={'meeting_id': meeting_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse({"message": success_message.get("UPDATE_SUCCESSFUL")}, status=status_code.HTTP_200_OK)

class ListRequestedMeetings(viewsets.ViewSet, viewsets.GenericViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = ListRequestedMeetingsSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ()

    def list(self, request):
        """
        Here the meetings request will be displayed and admin will either accept , reject or do it pending.
        """
        instance = ScheduleMeeting.objects.filter(state=3, admin_response__isnull=True
                                                  ).select_related('user').all().order_by('id')
        instance = self.filter_queryset(instance)
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(instance, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)

class ListUsersSignupRequest(viewsets.ViewSet, viewsets.GenericViewSet):
    permission_classes = (IsAdmin,)
    serializer_class = ListUsersSignupRequestSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('email', 'full_name')

    def list(self, request):
        """
        When the users signup then the list of newly signup users will be shown in the list.
        """
        instance = User.objects.filter(is_admin_approved=False).all().order_by('-created_at')
        instance = self.filter_queryset(instance)
        pagination_class = self.pagination_class()
        page = pagination_class.paginate_queryset(instance, request)
        if page is not None:
            serializer = self.serializer_class(instance=page, many=True)
            return SuccessResponse(pagination_class.get_paginated_response(serializer.data).data,
                                   status=status_code.HTTP_200_OK)
        serializer = self.serializer_class(instance, many=True)
        return SuccessResponse(serializer.data, status=status_code.HTTP_200_OK)


class UserRequests(viewsets.ViewSet):
    """
    Approve or delete the user
    """
    permission_classes = (IsAdmin,)
    serializer_class = UserRequestsSerializer

    def update(self, request):
        user_id = request.query_params.get('user_id')
        is_admin_approved = request.query_params.get('is_admin_approved')
        is_deleted = request.query_params.get('is_deleted')
        user_obj = User.all_objects.filter(id=user_id).first()
        if not user_obj:
            return Response(get_custom_error(status=400, message=validation_message.get("USER_NOT_FOUND"),
                                             error_location=validation_message.get("LOCATION")),
                            status=status_code.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(
            instance=user_obj, data=request.data, partial=True, context={"request": request,
                                                                         "user_id": user_id,
                                                                         "is_admin_approved": is_admin_approved,
                                                                         "is_deleted": is_deleted}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return SuccessResponse({"message": success_message.get('USER_UPDATED'),
                                }, status=status_code.HTTP_200_OK)
