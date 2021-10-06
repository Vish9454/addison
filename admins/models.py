from django.db import models
from core.models import BaseModel
from datetime import timedelta
# Create your models here.

class TimeSlot(BaseModel):
    """
    Admin will be able to add the time slot
    slots -- are in minutes
    amount -- is in dollars
    """
    TRAINING = 1
    OTHERS = 2
    COMPLIANCE_CHOICES = (
        (TRAINING, "Training"),
        (OTHERS, "Others"),
    )
    slots = models.DurationField(default=timedelta())
    amount = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    compliance = models.IntegerField(choices=COMPLIANCE_CHOICES, blank=True, null=True, verbose_name="Compliance")
