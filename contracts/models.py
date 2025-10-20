# contracts/models.py
from django.db import models
from django.core.exceptions import ValidationError
from companies.models import Company

class Contract(models.Model):
    """
    Represents a service contract between the catering company and a client company.
    """
    class ContractStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELED = "CANCELED", "Canceled"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=50,
        choices=ContractStatus.choices,
        default=ContractStatus.PENDING
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any specific terms, conditions, or notes for this contract."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        """
        Ensures that the end date is not before the start date.
        """
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("The contract end date cannot be before the start date.")

    def __str__(self):
        return f"Contract for {self.company.name} ({self.start_date} to {self.end_date})"