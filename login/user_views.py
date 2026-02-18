from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from .models import User, Booking, Rating, Transaction
from .forms import BookingForm, RatingForm, ProfileUpdateForm
from .utils import calculate_fare, estimate_distance, generate_transaction_id
from decimal import Decimal

# Decorator to ensure only users can access
def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'user':
            messages.error(request, 'Access denied. Users only.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# User Dashboard
@login_required
@user_required
def user_dashboard(request):
    user = request.user
    
    # Get active booking
    active_booking = Booking.objects.filter(
        user=user,
        status__in=['pending', 'accepted', 'in_progress']
    ).first()
    
    # Get recent bookings
    recent_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Statistics
    total_bookings = Booking.objects.filter(user=user).count()
    completed_bookings = Booking.objects.filter(user=user, status='completed').count()
    total_spent = Booking.objects.filter(
        user=user, 
        status='completed', 
        payment_status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    context = {
        'active_booking': active_booking,
        'recent_bookings': recent_bookings,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'total_spent': total_spent,
    }
    
    return render(request, 'user/dashboard.html', context)


# Book a Ride
@login_required
@user_required
def book_ride(request):
    # Check if user already has an active booking
    active_booking = Booking.objects.filter(
        user=request.user,
        status__in=['pending', 'accepted', 'in_progress']
    ).first()
    
    if active_booking:
        messages.warning(request, 'You already have an active booking. Please complete or cancel it first.')
        return redirect('booking_detail', booking_id=active_booking.id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.status = 'pending'
            
            # Calculate distance and fare if coordinates provided
            if all([booking.pickup_latitude, booking.pickup_longitude, 
                    booking.dropoff_latitude, booking.dropoff_longitude]):
                distance = estimate_distance(
                    booking.pickup_latitude, booking.pickup_longitude,
                    booking.dropoff_latitude, booking.dropoff_longitude
                )
                booking.distance = Decimal(str(distance))
                booking.fare = calculate_fare(distance, booking.vehicle_type)
            
            booking.save()
            messages.success(request, 'Ride booked successfully! Waiting for driver to accept.')
            return redirect('booking_detail', booking_id=booking.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingForm()
    
    return render(request, 'user/book_ride.html', {'form': form})


# Booking Detail
@login_required
@user_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'user/booking_detail.html', context)


# Booking History
@login_required
@user_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    
    return render(request, 'user/history.html', context)


# Cancel Booking
@login_required
@user_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status in ['pending', 'accepted']:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel this booking.')
    
    return redirect('booking_history')


# Rate Driver
@login_required
@user_required
def rate_driver(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status='completed')
    
    # Check if already rated
    if hasattr(booking, 'rating'):
        messages.info(request, 'You have already rated this ride.')
        return redirect('booking_history')
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.booking = booking
            rating.user = request.user
            rating.driver = booking.driver
            rating.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('booking_history')
    else:
        form = RatingForm()
    
    context = {
        'form': form,
        'booking': booking,
    }
    
    return render(request, 'user/rate_driver.html', context)


# Payment Page
@login_required
@user_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status='completed')
    
    if booking.payment_status == 'completed':
        messages.info(request, 'Payment already completed for this booking.')
        return redirect('booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        # Mark payment as completed
        booking.payment_status = 'completed'
        booking.save()
        
        # Create transaction record
        transaction = Transaction.objects.create(
            booking=booking,
            amount=booking.fare,
            payment_method=booking.payment_method,
            status='completed',
            transaction_id=generate_transaction_id(booking.id)
        )
        
        messages.success(request, 'Payment completed successfully!')
        return redirect('booking_detail', booking_id=booking.id)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'user/payment.html', context)


# User Profile
@login_required
@user_required
def user_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'user/profile.html', context)
