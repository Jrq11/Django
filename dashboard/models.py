from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='addroom/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
  
class Room(models.Model):
    ROOM_TYPES = [
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Triple', 'Triple'),
        ('Quad', 'Quad'),
    ]

    AVAILABILITY_STATUS = [
        ('Occupied', 'Occupied'),
        ('Vacant', 'Vacant'),
    ]

    room_number = models.IntegerField(unique=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    capacity = models.IntegerField()
    availability = models.CharField(max_length=17, choices=AVAILABILITY_STATUS, default='Vacant')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"
    
class Tenant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Linking User to Tenant
    room_number = models.ForeignKey(Room, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    lease_start = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15)

    def clean(self):
        # Validation for matching names
        if self.user:
            full_name_from_user = f"{self.user.first_name} {self.user.last_name}"
            if self.full_name != full_name_from_user:
                raise ValidationError("The full name does not match the user's first and last name.")
        super().clean()

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Tenant.objects.get(pk=self.pk)
            if old_instance.amount != self.amount:
                self._calculate_end_date()
        else:
            self._calculate_end_date()

        if not self.pk:
            self.room_number.availability = 'Occupied'
            self.room_number.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # If tenant is deleted, also delete associated user
        if self.user:
            self.user.delete()

        # Set room availability back to 'Vacant'
        self.room_number.availability = 'Vacant'
        self.room_number.save()

        super().delete(*args, **kwargs)

    def _calculate_end_date(self):
        base_amount = 2500  # Base amount for lease calculation
        months_duration = int(self.amount // base_amount)

        if months_duration > 0:
            self.end_date = self.lease_start + relativedelta(months=months_duration)
        else:
            self.end_date = self.lease_start + relativedelta(months=1)

    def __str__(self):
        return self.full_name

class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,  null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('overdue', 'Overdue')])
    reference_number = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Payment {self.reference_number} for {self.tenant.full_name}"


    
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']