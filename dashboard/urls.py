from django.urls import path
from .views import LandlordDashboardView, reports, payments, RoomListView, tenants, sales, AddRoomView,logout_view,RoomDeleteView,LandlordChatView,TenantCreateView, edit_tenant, add_payment, edit_report
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from . import views

app_name = 'landlord'

urlpatterns = [
   path('dashboard/', LandlordDashboardView.as_view(), name='main_dashboard'),
   path('Reports/', reports, name='reports'),
   path('edit_report/', edit_report, name='edit_report'),
   path('Payments/', payments, name='payments'),
   path('rooms/', RoomListView.as_view(), name='rooms'),
   path('Tenants/', tenants, name='tenants'),
   path('Sales/', sales, name='sales'),
   path('add-room/', AddRoomView.as_view(), name='add-room'),
   path("logout/", logout_view, name="logout"),
   path('rooms/edit/<int:room_id>/', views.edit_room, name='edit_room'),
   path('room/delete/<int:room_id>/', RoomDeleteView.as_view(), name='room-delete'),
   path('messages/', LandlordChatView.as_view(), name='message'),
   path('messages/<int:user_id>/', LandlordChatView.as_view(), name='message_with_user'),
   path('add-tenant/', TenantCreateView.as_view(), name='add_tenant'),
   #path('edit-form/<str:room_number>/', views.RoomFormView.as_view(), name='room_form'),
   path('edit-tenant/<int:tenant_id>/', edit_tenant, name='edit_tenant'),
   path('add_payment/', add_payment, name='add_payment'),

   

]