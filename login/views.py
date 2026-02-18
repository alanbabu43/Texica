from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import User, Vehicle, Booking, Rating, Transaction
from .forms import UserRegistrationForm, DriverRegistrationForm, LoginForm

# Create your views here.

# Landing Page
def index(request):
    if request.user.is_authenticated:
        # Redirect based on role
        if request.user.is_superuser or request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'driver':
            return redirect('driver_dashboard')
        else:
            return redirect('user_dashboard')
    return render(request, 'index.html')


# User Registration
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.role = 'user'
            user.status = 'active'
            user.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register_user.html', {'form': form})


# Driver Registration
def register_driver(request):
    if request.method == 'POST':
        form = DriverRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.role = 'driver'
            user.status = 'active'
            user.save()
            
            # Create vehicle
            vehicle = Vehicle.objects.create(
                driver=user,
                vehicle_type=form.cleaned_data['vehicle_type'],
                registration_number=form.cleaned_data['registration_number'],
                model=form.cleaned_data['model'],
                color=form.cleaned_data['color'],
                capacity=form.cleaned_data['capacity'],
                year=form.cleaned_data.get('year'),
                is_verified=False  # Admin needs to verify
            )
            
            messages.success(request, 'Registration successful! Your vehicle will be verified by admin. Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DriverRegistrationForm()
    
    return render(request, 'auth/register_driver.html', {'form': form})


# Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if user.status == 'active':
                    # Check if driver is verified
                    if user.role == 'driver':
                        try:
                            if not user.vehicle.is_verified:
                                messages.error(request, 'Your account is pending verification. Please wait for admin approval.')
                                return redirect('login')
                        except Vehicle.DoesNotExist:
                            messages.error(request, 'Driver account has no vehicle details. Please contact admin.')
                            return redirect('login')
                            
                    auth_login(request, user)
                    messages.success(request, f'Welcome back, {user.fullname}!')
                    
                    # Redirect based on role
                    if user.role == 'admin' or user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.role == 'driver':
                        return redirect('driver_dashboard')
                    else:
                        return redirect('user_dashboard')
                else:
                    messages.error(request, 'Your account has been blocked. Please contact admin.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')
