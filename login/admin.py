from django.contrib import admin
from .models import User, Vehicle, Booking, Rating, Transaction

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'fullname', 'phone', 'role', 'status', 'is_available']
    list_filter = ['role', 'status', 'is_available']
    search_fields = ['email', 'fullname', 'phone']
    ordering = ['-id']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'driver', 'vehicle_type', 'model', 'color', 'is_verified']
    list_filter = ['vehicle_type', 'is_verified']
    search_fields = ['registration_number', 'model', 'driver__fullname']
    ordering = ['-created_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'driver', 'status', 'vehicle_type', 'fare', 'payment_status', 'created_at']
    list_filter = ['status', 'vehicle_type', 'payment_method', 'payment_status']
    search_fields = ['user__fullname', 'driver__fullname', 'pickup_location', 'dropoff_location']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'user', 'driver', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__fullname', 'driver__fullname', 'review_text']
    ordering = ['-created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'amount', 'payment_method', 'status', 'transaction_id', 'timestamp']
    list_filter = ['payment_method', 'status']
    search_fields = ['transaction_id', 'booking__id']
    ordering = ['-timestamp']
