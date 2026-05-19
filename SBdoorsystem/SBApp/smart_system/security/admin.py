from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AccessLog

# Register the custom user
admin.site.register(CustomUser, UserAdmin)

# Register the access log so we can view the history
admin.site.register(AccessLog)