from django.urls import path
from .views import UserCreate, landing_page, register, login_view, validate_email, logout_view

urlpatterns = [
    path('register-api/', UserCreate.as_view(), name='user-register-api'),
    path('', landing_page, name='landing_page'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('validate-email/', validate_email, name='validate_email'),  
]
