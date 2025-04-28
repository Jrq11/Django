from django.urls import path
from .views import CustomLoginView,signUp,verify_otp, resend_otp
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', signUp, name='signup'),
    path('email_otp/', verify_otp, name='email_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
]