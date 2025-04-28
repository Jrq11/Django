from django.urls import path
from .views import TenantDashboardView,profile,TenantChatView,payment,maintenance,logout_view,maintenance_req,review_request,edit_profile
from . import views
app_name = 'tenant'

urlpatterns = [
    path('dashboard/', TenantDashboardView.as_view(), name='dashboard'),
    path('Profile/', profile, name='profile'),
    path('edit-profile/',edit_profile, name='edit_profile'),
    path('messages/', TenantChatView.as_view(), name='message'),
    path('messages/<int:user_id>/', TenantChatView.as_view(), name='message_with_user'),
    path('payment/', payment, name='payment'),
    path('maintenance/', maintenance, name='maintenance'),
    path("logout/", logout_view, name="logout"),
    path('maintenance/request/', maintenance_req, name='maintenance_req'),
    path('maintenance/review/', views.review_request, name='review_request'),
]
