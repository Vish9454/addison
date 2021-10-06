from django.db import models

# Create your models here.
class BaseModel(models.Model):
    """
    Base models to save the common properties such as:
        created_at, updated_at, is_deleted.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Last Updated At')
    is_deleted = models.BooleanField('Is Deleted', default=False)

    class Meta:
        abstract = True
        verbose_name = 'BaseModel'
        index_together = ["created_at", "updated_at"]