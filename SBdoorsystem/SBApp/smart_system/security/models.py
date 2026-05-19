from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import date

# 1. Our Custom User Model
class CustomUser(AbstractUser):
    # Existing fields
    is_employee = models.BooleanField(default=False)
    is_security = models.BooleanField(default=False)
    is_active_in_booth = models.BooleanField(default=False)
    is_active_guard = models.BooleanField(default=False)
    
    # NEW FIELDS for the command center & registration
    fullname = models.CharField(max_length=150, null=True, blank=True)
    user_id = models.CharField(max_length=10, unique=True, null=True, blank=True) # e.g., SM1234
    phone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, null=True, blank=True) # 'security' or 'employee'
    birthday = models.DateField(null=True, blank=True)
    post = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.username
    @property
    def age(self):
        if self.birthday:
            today = date.today()
            # Calcule l'âge exact en fonction de la date du jour
            return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        return "N/A"

# 2. Our Access History Log Model
class AccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=50) # e.g., "Telegram", "MIT App", "QR Code"
    action = models.CharField(max_length=50) # e.g., "Door Opened", "Access Denied"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} via {self.method} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
