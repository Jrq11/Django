from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class IssueType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('fixed', 'Fixed'),
    ]
    
    
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None)
    locations = models.ManyToManyField('Location', blank=True)
    issues = models.ManyToManyField('IssueType', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()
    requested_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Request at {self.requested_at.strftime('%Y-%m-%d %I:%M %p')}"
    
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')

    # User Info
    first_name = models.CharField(max_length=100, blank=True, null=True)  # Make optional
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)  # Make optional
    birthday = models.DateField(blank=True, null=True)  # Make optional
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)  # Make optional
    phone_no = models.CharField(max_length=20, blank=True, null=True)  # Make optional
    address = models.TextField(blank=True, null=True)  # Make optional
    email = models.EmailField(blank=True, null=True)  # Make optional

    # Guardian Info
    guardian_name = models.CharField(max_length=200, blank=True, null=True)  # Make optional
    guardian_phone_no = models.CharField(max_length=20, blank=True, null=True)  # Make optional
    guardian_address = models.TextField(blank=True, null=True)  # Make optional
    guardian_email = models.CharField(blank=True, null=True)  # Make optional

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        # Automatically sync User's first_name, last_name, and email with UserProfile
        self.first_name = self.user.first_name
        self.last_name = self.user.last_name
        self.email = self.user.email
        super(UserProfile, self).save(*args, **kwargs)