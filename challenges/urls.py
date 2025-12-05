from django.urls import path
from . import views
from .vulnerable_views import (
    vulnerable_file_read,
    vulnerable_command_injection,
    vulnerable_directory_listing,
    vulnerable_file_download,
    vulnerable_sql_injection,
    vulnerable_xxe,
    vulnerable_info_disclosure,
    vulnerable_robots_txt,
)
from .sql_injection_challenge import (
    sqli_challenge_home,
    sqli_challenge_login,
    sqli_challenge_hint,
    sqli_challenge_source,
    sqli_challenge_reset,
)
from .jwt_challenge import (
    jwt_challenge_home,
    jwt_challenge_redirect,
)

# Import SQL injection views into main views module
views.sqli_challenge_home = sqli_challenge_home
views.sqli_challenge_login = sqli_challenge_login
views.sqli_challenge_hint = sqli_challenge_hint
views.sqli_challenge_source = sqli_challenge_source
views.sqli_challenge_reset = sqli_challenge_reset

# Import JWT challenge views
views.jwt_challenge_home = jwt_challenge_home
views.jwt_challenge_redirect = jwt_challenge_redirect

app_name = 'challenges'

urlpatterns = [
    path('', views.challenge_list, name='list'),
    path('<int:challenge_id>/', views.challenge_detail, name='detail'),
    path('<int:challenge_id>/admin/', views.admin_challenge_detail, name='admin_detail'),
    path('<int:challenge_id>/submit/', views.submit_flag, name='submit'),
    path('<int:challenge_id>/download/', views.download_challenge_file, name='download'),
    path('hint/<int:hint_id>/view/', views.view_hint, name='view_hint'),
    
    # Vulnerable endpoints for server-side flag challenges
    path('vulnerable/<int:challenge_id>/read', vulnerable_file_read, name='vuln_file_read'),
    path('vulnerable/<int:challenge_id>/ping', vulnerable_command_injection, name='vuln_cmd_injection'),
    path('vulnerable/<int:challenge_id>/files', vulnerable_directory_listing, name='vuln_dir_listing'),
    path('vulnerable/<int:challenge_id>/download', vulnerable_file_download, name='vuln_file_download'),
    path('vulnerable/<int:challenge_id>/login', vulnerable_sql_injection, name='vuln_sql'),
    path('vulnerable/<int:challenge_id>/xml', vulnerable_xxe, name='vuln_xxe'),
    path('vulnerable/<int:challenge_id>/debug', vulnerable_info_disclosure, name='vuln_info'),
    path('vulnerable/<int:challenge_id>/robots.txt', vulnerable_robots_txt, name='vuln_robots'),
    
    # SQL Injection Challenge - Separate web app
    path('sqli/<int:challenge_id>/', views.sqli_challenge_home, name='sqli_home'),
    path('sqli/<int:challenge_id>/login', views.sqli_challenge_login, name='sqli_login'),
    path('sqli/<int:challenge_id>/hints', views.sqli_challenge_hint, name='sqli_hints'),
    path('sqli/<int:challenge_id>/source', views.sqli_challenge_source, name='sqli_source'),
    path('sqli/<int:challenge_id>/reset', views.sqli_challenge_reset, name='sqli_reset'),
    
    # JWT Challenge - Cookie/Storage based
    path('jwt/<int:challenge_id>/', views.jwt_challenge_home, name='jwt_home'),
    path('jwt/<int:challenge_id>/secret', views.jwt_challenge_redirect, name='jwt_secret'),
]