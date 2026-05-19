from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This tells Django to send all web traffic to your security app's urls.py
    path('', include('security.urls')), 
]