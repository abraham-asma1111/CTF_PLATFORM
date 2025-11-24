from django.urls import path
from . import views

app_name = 'challenges'

urlpatterns = [
    path('', views.challenge_list, name='list'),
    path('<int:challenge_id>/', views.challenge_detail, name='detail'),
    path('<int:challenge_id>/submit/', views.submit_flag, name='submit'),
    path('<int:challenge_id>/download/', views.download_challenge_file, name='download'),
]