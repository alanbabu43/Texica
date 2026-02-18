from django import forms
from .models import User, Vehicle, Booking, Rating
from django.core.validators import RegexValidator

# User Registration Form
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm password'
    }))
    
    class Meta:
        model = User
        fields = ['fullname', 'email', 'phone', 'address', 'profile']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}),
            'profile': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data


# Driver Registration Form
class DriverRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm password'
    }))
    
    # Vehicle fields
    vehicle_type = forms.ChoiceField(
        choices=Vehicle.VEHICLE_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    registration_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration Number'})
    )
    model = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vehicle Model'})
    )
    color = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vehicle Color'})
    )
    capacity = forms.IntegerField(
        initial=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Seating Capacity'})
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Manufacturing Year'})
    )
    
    class Meta:
        model = User
        fields = ['fullname', 'email', 'phone', 'address', 'profile']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}),
            'profile': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data


# Login Form
class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


# Booking Form
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['pickup_location', 'pickup_latitude', 'pickup_longitude', 
                  'dropoff_location', 'dropoff_latitude', 'dropoff_longitude',
                  'vehicle_type', 'payment_method', 'notes']
        widgets = {
            'pickup_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pickup Location',
                'id': 'pickup-location'
            }),
            'pickup_latitude': forms.HiddenInput(attrs={'id': 'pickup-lat'}),
            'pickup_longitude': forms.HiddenInput(attrs={'id': 'pickup-lng'}),
            'dropoff_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dropoff Location',
                'id': 'dropoff-location'
            }),
            'dropoff_latitude': forms.HiddenInput(attrs={'id': 'dropoff-lat'}),
            'dropoff_longitude': forms.HiddenInput(attrs={'id': 'dropoff-lng'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes (optional)',
                'rows': 3
            }),
        }


# Rating Form
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'review_text']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Share your experience (optional)',
                'rows': 4
            }),
        }


# Profile Update Form
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['fullname', 'phone', 'address', 'profile']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile': forms.FileInput(attrs={'class': 'form-control'}),
        }


# Vehicle Update Form
class VehicleUpdateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_type', 'registration_number', 'model', 'color', 'capacity', 'year']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
        }
