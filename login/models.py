from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# Custom user model
class User(AbstractUser):
    email = models.EmailField(unique=True)  
    phone = models.CharField(max_length=15, null=True, blank=True)
    fullname = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField()
    profile = models.ImageField(upload_to="profile/", null=True, blank=True)
    role = models.CharField(max_length=100, null=True, blank=True)  # admin, user, driver
    status = models.CharField(max_length=100, default='active')  # active, blocked
    is_available = models.BooleanField(default=False)  # For drivers - online/offline
    username = None

    objects = CustomUserManager()

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.fullname if self.fullname else self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


# Vehicle Model
class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('auto', 'Auto Rickshaw'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('luxury', 'Luxury Car'),
    ]
    
    driver = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vehicle')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    registration_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    capacity = models.IntegerField(default=4)
    year = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle'
    
    def __str__(self):
        return f"{self.vehicle_type} - {self.registration_number}"


# Booking Model
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('online', 'Online'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_bookings')
    
    pickup_location = models.CharField(max_length=255)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    dropoff_location = models.CharField(max_length=255)
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    vehicle_type = models.CharField(max_length=20, choices=Vehicle.VEHICLE_TYPES)
    
    pickup_time = models.DateTimeField(default=timezone.now)
    accepted_time = models.DateTimeField(null=True, blank=True)
    started_time = models.DateTimeField(null=True, blank=True)
    completed_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    distance = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # in km
    fare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, default='pending')  # pending, completed
    
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.fullname} - {self.status}"


# Rating Model
class Rating(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rating'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating {self.rating}/5 for {self.driver.fullname}"


# Transaction Model
class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Booking.PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'transaction'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Transaction #{self.id} - ₹{self.amount} - {self.status}"