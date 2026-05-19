from django.urls import path
from . import views

urlpatterns = [
    path('',                  views.login_view,             name='home'),
    path('login/',            views.login_view,             name='login'),
    path('register/',         views.register_view,          name='register'),
    path('dashboard/security/', views.sm_dashboard_view,   name='sm_dashboard'),
    path('dashboard/employee/', views.employee_dashboard_view, name='employee_dashboard'),
    path('trigger-alert/',    views.trigger_emergency_alert, name='trigger_alert'),
    path('logout/',           views.logout_view,            name='logout'),
    path('toggle-duty/',      views.toggle_duty,            name='toggle_duty'),
    path('log-access/',       views.log_access_view,        name='log_access'),
path('security/webcam-feed/', views.webcam_feed, name='webcam_feed'),
]
