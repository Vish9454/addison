from django.conf.urls import url
from admins import views as admin_views
from django.urls import path

urlpatterns =[
    path('timeslot', admin_views.TimeSlots.as_view({'get': 'list'}), name='time-slots'),  # 'post': 'create' add in prod
    path("retrievetimeslot/<int:timeslot_id>", admin_views.TimeSlots.as_view({"get": "retrieve"}),name="retrieve-slots"),
    path("updatetimeslot/<int:timeslot_id>", admin_views.TimeSlots.as_view({"put":"update"}),name="update-slots"),

    url('^signup$', admin_views.AdminSignUp.as_view({'post': 'create'}), name='create-admin'),

    path('dashboardcountings', admin_views.DashboardCountings.as_view({'get': 'list'}), name='dashboard-countings'),
    path('dashboardgraph', admin_views.DashboardGraph.as_view({'get': 'list'}), name='dashboard-graph'),

    # User Management
    path('listusers', admin_views.ListUsers.as_view({'get': 'list'}), name='list-users'),
    url('^signupuserbyadmin$', admin_views.UserSignUpByAdmin.as_view({'post': 'create'}), name='create-user-by-admin'),
    path('meetinglist', admin_views.ListMeetingsByState.as_view({'get': 'list'}), name='list-meetings'),
    path('toogleuserstate', admin_views.ToggleUserState.as_view({'put': 'update'}), name='user-toogle'),

    # Schedules
    path('upcomingmeetinglist', admin_views.ListUpcomingMeetings.as_view({'get': 'list'}), name='list-meetings'),
    path("retrieveuser/<int:user_id>", admin_views.UserRetrieve.as_view({"get": "retrieve"}),
         name="retrieve-user"),
    path("retrievemeet/<int:meet_id>", admin_views.MeetRetrieve.as_view({"get": "retrieve"}),
         name="retrieve-meet"),
    path('meetupdate/<int:meeting_id>', admin_views.MeetingUpdate.as_view({'put': 'update'}), name='meet-update'),
    path('requestmeetings', admin_views.ListRequestedMeetings.as_view({'get': 'list'}), name='list-meetings'),
    path('newuserrequest', admin_views.ListUsersSignupRequest.as_view({'get': 'list'}), name='list-user'),
    path('userrequests', admin_views.UserRequests.as_view({'put': 'update'}), name='user-update'),

]