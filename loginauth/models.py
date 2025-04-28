from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loginauth_profile')
    terms_accepted = models.BooleanField(default=False)
    date_accepted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username
