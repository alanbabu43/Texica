from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from .models import User, Vehicle, Booking, Rating, Transaction
from .forms import ProfileUpdateForm, VehicleUpdateForm
from .utils import calculate_fare
from decimal import Decimal

# Decorator to ensure only drivers can access
def driver_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'driver':
            messages.error(request, 'Access denied. Drivers only.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# Driver Dashboard
@login_required
@driver_required
def driver_dashboard(request):
    driver = request.user
    
    # Get active ride
    active_ride = Booking.objects.filter(
        driver=driver,
        status__in=['accepted', 'in_progress']
    ).first()
    
    # Get recent completed rides
    recent_rides = Booking.objects.filter(
        driver=driver,
        status='completed'
    ).order_by('-completed_time')[:5]
    
    # Statistics
    total_rides = Booking.objects.filter(driver=driver, status='completed').count()
    total_earnings = Booking.objects.filter(
        driver=driver,
        status='completed',
        payment_status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    # Average rating
    avg_rating = Rating.objects.filter(driver=driver).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Today's earnings
    from datetime import date
    today_earnings = Booking.objects.filter(
        driver=driver,
        status='completed',
        completed_time__date=date.today()
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    # Pending ride requests count
    pending_requests = Booking.objects.filter(
        status='pending',
        vehicle_type=driver.vehicle.vehicle_type if hasattr(driver, 'vehicle') else None
    ).count()
    
    context = {
        'active_ride': active_ride,
        'recent_rides': recent_rides,
        'total_rides': total_rides,
        'total_earnings': total_earnings,
        'avg_rating': round(avg_rating, 1),
        'today_earnings': today_earnings,
        'pending_requests': pending_requests,
        'is_available': driver.is_available,
    }
    
    return render(request, 'driver/dashboard.html', context)


# Toggle Availability
@login_required
@driver_required
def toggle_availability(request):
    driver = request.user
    driver.is_available = not driver.is_available
    driver.save()
    
    status = 'online' if driver.is_available else 'offline'
    messages.success(request, f'You are now {status}.')
    
    return redirect('driver_dashboard')


# Available Rides
@login_required
@driver_required
def available_rides(request):
    driver = request.user
    
    # Check if driver has a vehicle
    if not hasattr(driver, 'vehicle'):
        messages.error(request, 'Please add your vehicle details first.')
        return redirect('driver_profile')
    
    # Check if driver is available
    if not driver.is_available:
        messages.warning(request, 'You are currently offline. Please go online to see ride requests.')
        return redirect('driver_dashboard')
    
    # Check if driver already has an active ride
    active_ride = Booking.objects.filter(
        driver=driver,
        status__in=['accepted', 'in_progress']
    ).first()
    
    if active_ride:
        messages.info(request, 'You already have an active ride.')
        return redirect('active_ride', booking_id=active_ride.id)
    
    # Get pending bookings matching driver's vehicle type
    available_bookings = Booking.objects.filter(
        status='pending',
        vehicle_type=driver.vehicle.vehicle_type
    ).order_by('-created_at')
    
    context = {
        'bookings': available_bookings,
    }
    
    return render(request, 'driver/available_rides.html', context)


# Accept Ride
@login_required
@driver_required
def accept_ride(request, booking_id):
    driver = request.user
    booking = get_object_or_404(Booking, id=booking_id, status='pending')
    
    # Check if driver already has an active ride
    active_ride = Booking.objects.filter(
        driver=driver,
        status__in=['accepted', 'in_progress']
    ).first()
    
    if active_ride:
        messages.error(request, 'You already have an active ride.')
        return redirect('active_ride', booking_id=active_ride.id)
    
    # Accept the booking
    booking.driver = driver
    booking.status = 'accepted'
    booking.accepted_time = timezone.now()
    booking.save()
    
    messages.success(request, 'Ride accepted! Please proceed to pickup location.')
    return redirect('active_ride', booking_id=booking.id)


# Reject Ride
@login_required
@driver_required
def reject_ride(request, booking_id):
    # Just redirect back - driver simply doesn't accept
    messages.info(request, 'Ride request skipped.')
    return redirect('available_rides')


# Active Ride
@login_required
@driver_required
def active_ride(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, driver=request.user)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'driver/active_ride.html', context)


# Start Ride
@login_required
@driver_required
def start_ride(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, driver=request.user, status='accepted')
    
    booking.status = 'in_progress'
    booking.started_time = timezone.now()
    booking.save()
    
    messages.success(request, 'Ride started!')
    return redirect('active_ride', booking_id=booking.id)


# Complete Ride
@login_required
@driver_required
def complete_ride(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, driver=request.user, status='in_progress')
    
    if request.method == 'POST':
        # Get actual distance and calculate fare
        actual_distance = request.POST.get('actual_distance')
        
        if actual_distance:
            booking.distance = Decimal(actual_distance)
            booking.fare = calculate_fare(Decimal(actual_distance), booking.vehicle_type)
        
        booking.status = 'completed'
        booking.completed_time = timezone.now()
        booking.save()
        
        messages.success(request, 'Ride completed successfully!')
        return redirect('driver_dashboard')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'driver/complete_ride.html', context)


# Earnings History
@login_required
@driver_required
def earnings_history(request):
    driver = request.user
    
    # Get all completed rides
    completed_rides = Booking.objects.filter(
        driver=driver,
        status='completed'
    ).order_by('-completed_time')
    
    # Calculate total earnings
    total_earnings = completed_rides.aggregate(total=Sum('fare'))['total'] or 0
    paid_earnings = completed_rides.filter(payment_status='completed').aggregate(total=Sum('fare'))['total'] or 0
    pending_earnings = total_earnings - paid_earnings
    
    context = {
        'rides': completed_rides,
        'total_earnings': total_earnings,
        'paid_earnings': paid_earnings,
        'pending_earnings': pending_earnings,
    }
    
    return render(request, 'driver/earnings.html', context)


# Ride Detail (Driver)
@login_required
@driver_required
def ride_detail_driver(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, driver=request.user, status='completed')
    
    context = {
        'ride': booking,
    }
    
    return render(request, 'driver/earning_detail.html', context)


# Driver Profile
@login_required
@driver_required
def driver_profile(request):
    driver = request.user
    
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=driver)
        
        # Check if driver has a vehicle
        if hasattr(driver, 'vehicle'):
            vehicle_form = VehicleUpdateForm(request.POST, instance=driver.vehicle)
        else:
            vehicle_form = VehicleUpdateForm(request.POST)
        
        if profile_form.is_valid() and vehicle_form.is_valid():
            profile_form.save()
            
            if hasattr(driver, 'vehicle'):
                vehicle_form.save()
            else:
                vehicle = vehicle_form.save(commit=False)
                vehicle.driver = driver
                vehicle.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('driver_profile')
    else:
        profile_form = ProfileUpdateForm(instance=driver)
        vehicle_form = VehicleUpdateForm(instance=driver.vehicle) if hasattr(driver, 'vehicle') else VehicleUpdateForm()
    
    # Get ratings
    ratings = Rating.objects.filter(driver=driver).order_by('-created_at')[:10]
    avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    
    context = {
        'profile_form': profile_form,
        'vehicle_form': vehicle_form,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1),
    }

    return render(request, 'driver/profile.html', context)


# Update Booking Estimated Fare
@login_required
@driver_required
def update_booking_est_fare(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, driver=request.user)
        
        try:
            import json
            data = json.loads(request.body)
            distance_km = Decimal(str(data.get('distance_km', 0)))
            
            if distance_km > 0:
                # Update distance
                booking.distance = distance_km.quantize(Decimal('0.01'))
                
                # Recalculate fare
                booking.fare = calculate_fare(distance_km, booking.vehicle_type)
                
                booking.save()
                
                return JsonResponse({
                    'status': 'success',
                    'distance': float(booking.distance),
                    'fare': float(booking.fare)
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
