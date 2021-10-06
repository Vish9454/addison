"""user related """
from django.conf.urls import url
from django.urls import path
from accounts import views as user_views

urlpatterns = [
    url('^signup$', user_views.UserSignUp.as_view({'post': 'create'}), name='create-users'),
    url('^verifyemail$', user_views.VerifyEmail.as_view({'post': 'create'}),
        name='verify-email'),
    url('^login$', user_views.Login.as_view({'post': 'create'}), name='log-in'),
    url('^forgotpassword$', user_views.UserForgotPassword.as_view({'post': 'create'}), name='forgot-password'),
    url('^resetpassword$', user_views.UserResetPassword.as_view({'post': 'create'}),
        name='reset-password'),
    url('^resendverifyemail$', user_views.ResendVerifyEmail.as_view({'post': 'create'}),
        name='resend-verify-email$'),
    path('passwordchange', user_views.ChangePassword.as_view({'put': 'update'}),
         name='change-password'),
    url('^profileverifyemail$', user_views.VerifyEmailUserUpdate.as_view({'post': 'create'}),
        name='verify-email-update-profile'),
    # Profile update
    path("profileupdate/<int:user_id>", user_views.UpdateUserProfile.as_view({"put": "update"}),
         name="profile-update", ),

    # Schedule meeting API's
    path('meeting', user_views.ScheduleMeetings.as_view({'post': 'create', 'get': 'list'}), name='meet-schedule'),
    path('updatemeeting/<int:meeting_id>', user_views.ScheduleMeetings.as_view({'put': 'update'}),
         name='meet-schedule-update'),
    path('retrievemeeting/<int:meeting_id>', user_views.ScheduleMeetings.as_view({'get': 'retrieve'}),
         name='meet-schedule-retrieve'),
    path('cancelmeeting/<int:meeting_id>', user_views.CancelMeeting.as_view({'put': 'update'}),
         name='meet-schedule-cancel'),
    path('countrylist', user_views.ListRegionCountry.as_view({'get': 'list'}),name='country-list'),
    path('isverifiedemail', user_views.IsEmailVerifiedResendLink.as_view({'post': 'create'}),name='is-email-verified'),

    path('fcmtokendelete', user_views.DeleteFCMToken.as_view({'delete': 'destroy'}),
         name='fcm-token-delete'),
    path('notificationlist', user_views.NotificationList.as_view({'get': 'list'}), name='Notification-list'),

]
