from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, Vehicle, Booking, Rating, Transaction

# Decorator to ensure only admins can access
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Allow if user is admin role OR superuser
        if request.user.role != 'admin' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Admins only.')
            return redirect('login')
            
        return view_func(request, *args, **kwargs)
    return wrapper


# Admin Dashboard
@login_required
@admin_required
def admin_dashboard(request):
    # Statistics
    total_users = User.objects.filter(role='user').count()
    total_drivers = User.objects.filter(role='driver').count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.filter(
        status='completed',
        payment_status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    # Today's stats
    today = timezone.now().date()
    today_bookings = Booking.objects.filter(created_at__date=today).count()
    today_revenue = Booking.objects.filter(
        completed_time__date=today,
        status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    # Active bookings
    active_bookings = Booking.objects.filter(
        status__in=['pending', 'accepted', 'in_progress']
    ).count()
    
    # Pending driver verifications
    pending_verifications = Vehicle.objects.filter(is_verified=False).count()
    
    # Recent bookings
    recent_bookings = Booking.objects.all().order_by('-created_at')[:10]
    
    # Booking status distribution
    status_distribution = Booking.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'total_drivers': total_drivers,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'today_bookings': today_bookings,
        'today_revenue': today_revenue,
        'active_bookings': active_bookings,
        'pending_verifications': pending_verifications,
        'recent_bookings': recent_bookings,
        'status_distribution': status_distribution,
    }
    
    return render(request, 'admin/dashboard.html', context)


# Manage Users
@login_required
@admin_required
def manage_users(request):
    users = User.objects.filter(role='user').order_by('-id')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(fullname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    
    return render(request, 'admin/users.html', context)


# User Detail
@login_required
@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id, role='user')
    bookings = Booking.objects.filter(user=user).order_by('-created_at')
    
    # User statistics
    total_bookings = bookings.count()
    completed_bookings = bookings.filter(status='completed').count()
    total_spent = bookings.filter(
        status='completed',
        payment_status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    context = {
        'user': user,
        'bookings': bookings,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'total_spent': total_spent,
    }
    
    return render(request, 'admin/user_detail.html', context)


# Block/Unblock User
@login_required
@admin_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if user.status == 'active':
        user.status = 'blocked'
        messages.success(request, f'{user.fullname} has been blocked.')
    else:
        user.status = 'active'
        messages.success(request, f'{user.fullname} has been unblocked.')
    
    user.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'manage_users'))


# Manage Drivers
@login_required
@admin_required
def manage_drivers(request):
    drivers = User.objects.filter(role='driver').select_related('vehicle').order_by('-id')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        drivers = drivers.filter(
            Q(fullname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(vehicle__registration_number__icontains=search_query)
        )
    
    # Filter by verification status
    verification_filter = request.GET.get('verified')
    if verification_filter == 'yes':
        drivers = drivers.filter(vehicle__is_verified=True)
    elif verification_filter == 'no':
        drivers = drivers.filter(vehicle__is_verified=False)
    
    context = {
        'drivers': drivers,
        'search_query': search_query,
        'verification_filter': verification_filter,
    }
    
    return render(request, 'admin/drivers.html', context)


# Driver Detail
@login_required
@admin_required
def driver_detail(request, driver_id):
    driver = get_object_or_404(User, id=driver_id, role='driver')
    bookings = Booking.objects.filter(driver=driver).order_by('-created_at')
    ratings = Rating.objects.filter(driver=driver).order_by('-created_at')
    
    # Driver statistics
    total_rides = bookings.filter(status='completed').count()
    total_earnings = bookings.filter(
        status='completed',
        payment_status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    
    context = {
        'driver': driver,
        'bookings': bookings,
        'ratings': ratings,
        'total_rides': total_rides,
        'total_earnings': total_earnings,
        'avg_rating': round(avg_rating, 1),
    }
    
    return render(request, 'admin/driver_detail.html', context)


# Verify Driver
@login_required
@admin_required
def verify_driver(request, driver_id):
    driver = get_object_or_404(User, id=driver_id, role='driver')
    
    if hasattr(driver, 'vehicle'):
        vehicle = driver.vehicle
        vehicle.is_verified = not vehicle.is_verified
        vehicle.save()
        
        status = 'verified' if vehicle.is_verified else 'unverified'
        messages.success(request, f'Driver {driver.fullname} has been {status}.')
    else:
        messages.error(request, 'Driver has no vehicle registered.')
    
    return redirect(request.META.get('HTTP_REFERER', 'manage_drivers'))


# Manage Bookings
@login_required
@admin_required
def manage_bookings(request):
    bookings = Booking.objects.all().select_related('user', 'driver').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        bookings = bookings.filter(created_at__date=date_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        bookings = bookings.filter(
            Q(id__icontains=search_query) |
            Q(user__fullname__icontains=search_query) |
            Q(driver__fullname__icontains=search_query) |
            Q(pickup_location__icontains=search_query) |
            Q(dropoff_location__icontains=search_query)
        )
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/bookings.html', context)


# Booking Detail (Admin)
@login_required
@admin_required
def booking_detail_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'admin/booking_detail.html', context)


# Manage Transactions
@login_required
@admin_required
def manage_transactions(request):
    transactions = Transaction.objects.all().select_related('booking', 'booking__user', 'booking__driver').order_by('-timestamp')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Filter by payment method
    method_filter = request.GET.get('method')
    if method_filter:
        transactions = transactions.filter(payment_method=method_filter)
    
    # Calculate totals
    total_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'transactions': transactions,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'total_amount': total_amount,
    }
    
    return render(request, 'admin/transactions.html', context)


# Reports
@login_required
@admin_required
def reports(request):
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Revenue over time (last 30 days)
    daily_revenue = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        revenue = Booking.objects.filter(
            completed_time__date=date,
            status='completed'
        ).aggregate(total=Sum('fare'))['total'] or 0
        daily_revenue.append({
            'date': date,
            'revenue': revenue
        })
    
    # Bookings by vehicle type
    vehicle_type_stats = Booking.objects.values('vehicle_type').annotate(
        count=Count('id'),
        revenue=Sum('fare')
    )
    
    # Top drivers
    top_drivers = User.objects.filter(role='driver').annotate(
        total_rides=Count('driver_bookings', filter=Q(driver_bookings__status='completed')),
        total_earnings=Sum('driver_bookings__fare', filter=Q(driver_bookings__status='completed'))
    ).order_by('-total_earnings')[:10]
    
    # Top users
    top_users = User.objects.filter(role='user').annotate(
        total_bookings=Count('bookings'),
        total_spent=Sum('bookings__fare', filter=Q(bookings__status='completed'))
    ).order_by('-total_spent')[:10]
    
    context = {
        'daily_revenue': daily_revenue,
        'vehicle_type_stats': vehicle_type_stats,
        'top_drivers': top_drivers,
        'top_users': top_users,
    }
    
    return render(request, 'admin/reports.html', context)
