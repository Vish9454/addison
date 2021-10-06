from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import (AbstractBaseUser, UserManager)
from core.models import BaseModel
from admins.models import TimeSlot
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class MyUserManager(BaseUserManager):
    """
    Inherits: BaseUserManager class
    """

    def create_user(self, email, password=None):
        """
        Create user with given email and password.
        :param email:
        :param password:
        :return:
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email))
        # set_password is used set password in encrypted form.
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Create and save the super user with given email and password.
        :param email:
        :param password:
        :return: user
        """
        user = self.create_user(email, password=password)
        user.is_superuser = True
        user.username = ""
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class ActiveUserManager(UserManager):
    """
        ActiveUserManager class to filter the deleted user.
    """

    def get_queryset(self):
        return super(ActiveUserManager, self).get_queryset().filter(is_active=True, is_deleted=False)


class ActiveObjectsManager(UserManager):
    """
        ActiveObjectsManager class to filter the deleted objs
    """

    def get_queryset(self):
        return super(ActiveObjectsManager, self).get_queryset().filter(is_deleted=False)


class User(AbstractBaseUser, BaseModel):
    """
    MyUser models used for the authentication process and it contains basic
     fields.
     Inherit : AbstractBaseUser, PermissionMixin, BaseModel
    """
    ADMIN = 1
    USER = 2
    ROLE = (
        (ADMIN, "Admin"),
        (USER, "User")
    )

    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='First Name')
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Last Name')
    full_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Full Name')
    email = models.EmailField(max_length=80, unique=True, blank=False, null=False, verbose_name='Email')
    phone_number = models.CharField(max_length=25, unique=False, blank=True, null=True,
                                    verbose_name='Phone Number')
    profile_image = models.CharField(max_length=255, blank=True, null=True, verbose_name='Profile Image')
    company = models.CharField(max_length=120, blank=True, null=True, verbose_name='Company name')
    address = models.CharField(max_length=300, blank=True, null=True, verbose_name="Address")

    user_role = models.IntegerField("User Role", choices=ROLE, default=USER)

    is_email_verified = models.BooleanField('Email Verified', default=False)
    is_admin_approved = models.BooleanField('Admin Approval', default=False)
    is_active = models.BooleanField('Active', default=True)
    is_staff = models.BooleanField('Is Staff', default=False)
    is_superuser = models.BooleanField('SuperUser', default=False)

    objects = ActiveUserManager()
    all_objects = ActiveObjectsManager()
    all_delete_objects = UserManager()
    my_user_manager = MyUserManager()
    USERNAME_FIELD = 'email'

    def has_perm(self, perm, obj=None):
        """
        has_perm method used to give permission to the user.
        :param perm:
        :param obj:
        :return: is_staff
        """
        return self.is_staff

    def has_module_perms(self, app_label):
        """
        method to give module permission to the superuser.
        :param app_label:
        :return: is_superuser
        """
        return self.is_superuser

    def __str__(self):
        """
        :return: email
        """
        return self.email

    def get_short_name(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        ordering = ['id']
        index_together = ["email", "phone_number", "updated_at"]


class AccountVerification(BaseModel):
    """
        AccountVerification models to save the account verification details.
    """
    EMAIL_VERIFICATION = 1
    FORGOT_PASSWORD = 2
    OTHER = 3
    VERIFY_CHOICE = (
        (EMAIL_VERIFICATION, "Verifiy Email"),
        (FORGOT_PASSWORD, "Forgot Password"),
        (OTHER, "Other")
    )
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_token')
    token = models.CharField(blank=False, max_length=100, verbose_name='Token')
    expired_at = models.DateTimeField(blank=False, verbose_name='Expired At')
    is_used = models.BooleanField('IsUsed', default=False)
    verification_type = models.IntegerField(choices=VERIFY_CHOICE, blank=False, verbose_name='Verification Type')

    class Meta:
        verbose_name = 'AccountVerification'


class CountryRegion(models.Model):
    region = models.CharField("region", max_length=50, null=True, blank=True)
    country = models.CharField("country", max_length=50, null=True, blank=True)


class Questionnaire(BaseModel):
    # these are the type of answers to the questions posted on app
    RADIO = 1
    TEXT = 2
    RADIO_TEXT = 3  # here radio button and description box , both are there
    DROP_DOWN_1 = 4
    DROP_DOWN_2 = 5  # ex = select country / then region , so there are 2 drop downs
    DROP_DOWN_3 = 6
    TYPE_CHOICES = (
        (RADIO, "Radio Button"),
        (TEXT, "Text"),
        (RADIO_TEXT, "Radio and Text both"),
        (DROP_DOWN_1, "Drop Down"),
        (DROP_DOWN_2, "Two Drop Down"),
        (DROP_DOWN_3, "Three Drop Down"),
    )
    EXPORT = 1
    IMPORT = 2
    RISK_ASSESSMENT = 3
    TRAINING = 4
    PCV = 5
    AMS = 6
    COMPLIANCE_CHOICES = (
        (EXPORT, "Export"),
        (IMPORT, "Import"),
        (RISK_ASSESSMENT, "Risk Assessment"),
        (TRAINING, "Training"),
        (PCV, "Product Certification and Validation"),
        (AMS, "Asia Market Services"),
    )
    EXPORT_PRODUCT = 1
    EXPORT_SERVICES = 2
    EXPORT_BOTH = 3
    AMS_CML = 4
    AMS_SCS = 5
    AMS_CMC = 6
    AMS_IML = 7
    SUBCATEGORY_CHOICE = (
        (EXPORT_PRODUCT, "Export Product"),
        (EXPORT_SERVICES, "Export Services"),
        (EXPORT_BOTH, "Export Both"),
        (AMS_CML, "China Market Liaison"),
        (AMS_SCS, "China Supply Chain Support"),
        (AMS_CMC, "China Market Compliance"),
        (AMS_IML, "India Market Liaison"),
    )
    questions = models.TextField(blank=True, null=True)
    type = models.IntegerField(choices=TYPE_CHOICES, blank=True, null=True, verbose_name='Type of answers')
    category = models.IntegerField(choices=COMPLIANCE_CHOICES, blank=True, null=True, verbose_name="Category of Compliance")
    subcategory = models.IntegerField(choices=SUBCATEGORY_CHOICE, blank=True, null=True, verbose_name="Subcategory of Compliance")

class ScheduleMeeting(BaseModel):
    """
    Meeting will be scheduled by the user
    """
    EXPORT = 1
    IMPORT = 2
    RISK_ASSESSMENT = 3
    TRAINING = 4
    PCV = 5
    AMS = 6
    COMPLIANCE_CHOICES = (
        (EXPORT, "Export"),
        (IMPORT, "Import"),
        (RISK_ASSESSMENT, "Risk Assessment"),
        (TRAINING, "Training"),
        (PCV, "Product Certification and Validation"),
        (AMS, "Asia Market Services"),
    )
    CREATED = 1
    CANCEL = 2
    PAYMENT_PROCESSED = 3
    COMPLETED = 4
    STATES = (
         (CREATED, "created"),
         (CANCEL, "cancel"),
         (PAYMENT_PROCESSED, "payment on hold"),  # payment is processed and this will count in upcoming meeting
         (COMPLETED, "completed"),
    )
    ACCEPT_ADMIN = 1
    REJECT_ADMIN = 2
    PENDING_ADMIN = 3
    RESCHEDULE_ADMIN = 4
    ADMIN_RESPONSES = (
        (ACCEPT_ADMIN, "Meeting accepted by Admin"),
        (REJECT_ADMIN, "Meeting rejected by Admin"),
        (PENDING_ADMIN, "Meeting pending by Admin"),
        (RESCHEDULE_ADMIN,"Meeting rescheduled by Admin")
    )

    ACCEPT_USER = 1
    REJECT_USER = 2
    PENDING_USER = 3
    USER_RESPONSE = (
        (ACCEPT_USER, "Meeting accepted by user"),
        (REJECT_USER, "Meeting rejected by user"),
        (PENDING_USER, "Meeting pending by user"),
    )

    SUBSCRIPTION = 1
    CARD = 2
    INVOICE_REQUEST = 3
    PAYMENT_CHOICES = (
        (SUBSCRIPTION, "Subscription"),
        (CARD, "Card"),
        (INVOICE_REQUEST, "Invoice request"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_meeting")
    question_answer = models.JSONField(null=True, blank=True, verbose_name="Questionnaire_id and Answers")
    compliance = models.IntegerField(choices=COMPLIANCE_CHOICES, blank=True, null=True, verbose_name="Compliance")
    # time slots
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, blank=True, null=True,related_name="timeslot_meeting")
    amount = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    meet_link = models.CharField("Meeting Link", max_length=200, null=True, blank=True)
    state = models.IntegerField("State", choices=STATES, default=CREATED)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    # this is the pdf uploaded by user
    complaince_challenge = models.CharField("Pdf file", max_length=200, null=True, blank=True)
    admin_response = models.IntegerField(choices=ADMIN_RESPONSES, blank=True, null=True, verbose_name="admin response")
    # here admin will give pdf file (ex=["/imgaes/hjshdjsjdh.pdf","jshjdh hjsdh"])and the desciption in an array
    consultant_feedback = ArrayField(models.CharField(max_length=800), blank=True, null=True)
    payment_via = models.IntegerField(choices=PAYMENT_CHOICES, blank=True, null=True, verbose_name="Payment Methods")
    cancellation_charge = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # payment by card related information
    card_id = models.CharField("Card Id", max_length=100, null=True, blank=True)
    payment_intent_id = models.CharField("Payment Intent Id", max_length=100, null=True, blank=True)
    user_response = models.IntegerField(choices=USER_RESPONSE, blank=True, null=True, verbose_name="user response")
    region_country = ArrayField(models.CharField(max_length=200), blank=True, null=True)

class DeviceManagement(BaseModel):
    """
        Model to map all the devices doctor logged in.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='user_device')
    device_uuid = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=500, null=True, blank=True)

class UserActivity(BaseModel):
    """Model to store request send from one user to another"""
    ADMIN_SEND_YOU_A_NOTIFICATION_ACCEPT_MEETING = 1
    ADMIN_SEND_YOU_A_NOTIFICATION_REJECT_MEETING = 2
    ADMIN_SEND_YOU_A_NOTIFICATION_RESCHEDULE_MEETING = 3
    ADMIN_SEND_YOU_A_NOTIFICATION__FOR_FEEDBACK = 4
    ACTIVITY_TYPES = (
        (ADMIN_SEND_YOU_A_NOTIFICATION_ACCEPT_MEETING, "Admin accepts the meeting"),
        (ADMIN_SEND_YOU_A_NOTIFICATION_REJECT_MEETING, "Admin rejects the meeting"),
        (ADMIN_SEND_YOU_A_NOTIFICATION_RESCHEDULE_MEETING, "Admin reschedules the meeting"),
        (ADMIN_SEND_YOU_A_NOTIFICATION__FOR_FEEDBACK, "Admin sends feeback"),
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_receiver")
    activity_type = models.IntegerField("Activity Type", choices=ACTIVITY_TYPES)
    title = models.CharField("title", max_length=100, null=True, blank=True)
    message = models.CharField("message", max_length=100, null=True, blank=True)
    payload = models.CharField("payload", max_length=600, null=True, blank=True)
    is_read = models.BooleanField("isread", default=False)