# p2p_trading/models/base_model.py

from django.db import models

class BaseModel(models.Model):
    """ Base model for all the common fields    """
    id = models.AutoField(primary_key=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete support
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        abstract = True  #  model abstract
        ordering = ['-created_at']  # default order top to down