from django.urls import path
from . import views, user_views, driver_views, admin_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Main & Auth
    path('', views.index, name='index'),
    path('register/', views.register_user, name='register_user'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User Routes
    path('user/dashboard/', user_views.user_dashboard, name='user_dashboard'),
    path('user/book/', user_views.book_ride, name='book_ride'),
    path('user/booking/<int:booking_id>/', user_views.booking_detail, name='booking_detail'),
    path('user/history/', user_views.booking_history, name='booking_history'),
    path('user/cancel/<int:booking_id>/', user_views.cancel_booking, name='cancel_booking'),
    path('user/rate/<int:booking_id>/', user_views.rate_driver, name='rate_driver'),
    path('user/payment/<int:booking_id>/', user_views.payment_page, name='payment_page'),
    path('user/profile/', user_views.user_profile, name='user_profile'),

    # Driver Routes
    path('driver/dashboard/', driver_views.driver_dashboard, name='driver_dashboard'),
    path('driver/availability/toggle/', driver_views.toggle_availability, name='toggle_availability'),
    path('driver/rides/available/', driver_views.available_rides, name='available_rides'),
    path('driver/ride/<int:booking_id>/', driver_views.active_ride, name='active_ride'),
    path('driver/ride/accept/<int:booking_id>/', driver_views.accept_ride, name='accept_ride'),
    path('driver/ride/reject/<int:booking_id>/', driver_views.reject_ride, name='reject_ride'),
    path('driver/ride/start/<int:booking_id>/', driver_views.start_ride, name='start_ride'),
    path('driver/ride/complete/<int:booking_id>/', driver_views.complete_ride, name='complete_ride'),
    path('driver/earnings/', driver_views.earnings_history, name='earnings_history'),
    path('driver/profile/', driver_views.driver_profile, name='driver_profile'),
    path('driver/ride/update-est-fare/<int:booking_id>/', driver_views.update_booking_est_fare, name='update_booking_est_fare'),

    # Admin Routes
    path('admin-panel/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', admin_views.manage_users, name='manage_users'),
    path('admin-panel/user/<int:user_id>/', admin_views.user_detail, name='user_detail'),
    path('admin-panel/user/toggle-status/<int:user_id>/', admin_views.toggle_user_status, name='toggle_user_status'),
    path('admin-panel/drivers/', admin_views.manage_drivers, name='manage_drivers'),
    path('admin-panel/driver/<int:driver_id>/', admin_views.driver_detail, name='driver_detail'),
    path('admin-panel/driver/verify/<int:driver_id>/', admin_views.verify_driver, name='verify_driver'),
    path('admin-panel/bookings/', admin_views.manage_bookings, name='manage_bookings'),
    path('admin-panel/booking/<int:booking_id>/', admin_views.booking_detail_admin, name='booking_detail_admin'),
    path('admin-panel/transactions/', admin_views.manage_transactions, name='manage_transactions'),
    path('admin-panel/reports/', admin_views.reports, name='reports'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)