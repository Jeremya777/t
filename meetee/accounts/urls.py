# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterWizard.as_view(), name='register_wizard'),
    path('login/', views.LoginWizard.as_view(), name='login_wizard'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),  # Aggiungi questa linea
    path('search_users/', views.search_users, name='search_users'),
    path('find_active_user', views.find_active_user, name='find_active_user'),
    path('send_connection_request/', views.send_connection_request, name='send_connection_request'),
    path('accept_connection/<int:from_user_id>/', views.accept_connection, name='accept_connection'),
    path('reject_connection/<int:from_user_id>/', views.reject_connection, name='reject_connection'),
    #path('close_session/', views.close_session, name='close_session'),
]
