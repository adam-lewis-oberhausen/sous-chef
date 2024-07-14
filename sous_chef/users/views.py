# users/views.py

from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework import generics
from .serializers import UserSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.validators import validate_email as validate_email_address
from django.core.exceptions import ValidationError

class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

def landing_page(request):
    if request.user.is_authenticated:  # Check if the user is already authenticated
        return redirect('chat-interface')    
    return render(request, 'users/landing_page.html')

def register(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            return HttpResponse("Passwords do not match.")
        
        user_data = {
            'email': email,
            'password': password
        }
        
        serializer = UserSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            return redirect('login')  # Redirect to the login page
        else:
            return HttpResponse("Registration failed.")
    return render(request, 'users/landing_page.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
        
        if not email or not password:
            return HttpResponse("Email and password are required.")
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat-interface')  # Redirect to the chat page
        else:
            return HttpResponse("Invalid login details.")
    return render(request, 'users/landing_page.html')

def logout_view(request):
    logout(request)
    return redirect('landing_page')

def validate_email(request):
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(email__iexact=email).exists()
    }
    try:
        validate_email_address(email)
        data['is_valid'] = True
    except ValidationError:
        data['is_valid'] = False
    return JsonResponse(data)
