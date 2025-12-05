from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/preferences/', views.update_preferences, name='update_preferences'),
    path('settings/notifications/', views.update_notifications, name='update_notifications'),
    path('settings/privacy/', views.update_privacy, name='update_privacy'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('send-verification/', views.send_verification_email, name='send_verification'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
]