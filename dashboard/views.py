from django.shortcuts import render, redirect, get_object_or_404
from .forms import ImageUploadForm, RoomForm,SignupForm, TenantForm, PaymentForm
from .models import Tenant, Room, ChatMessage, Payment
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count
from datetime import date
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.views.generic import TemplateView, ListView,CreateView,RedirectView,FormView
from django.views.generic.edit import UpdateView
from django.db.models import Q
from django.utils import timezone
import time
from tenant.models import MaintenanceRequest
import random
import string
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags

@method_decorator(login_required, name='dispatch')
class LandlordDashboardView(TemplateView):
    template_name = 'dashboard/main_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_date = date.today()
        current_year = current_date.year

        tenant_count = Tenant.objects.count()

        start_of_year = date(current_year, 1, 1)
        end_of_year = date(current_year, 12, 31)

        total_sales_for_year = Tenant.objects.filter(
            lease_start__lte=end_of_year,
            end_date__gte=start_of_year
        ).aggregate(total=Sum('amount'))['total'] or 0

        available_rooms = Room.objects.filter(availability='Vacant')
        total_unit = available_rooms.count()

        report_data = []
        maintenance_requests = MaintenanceRequest.objects.select_related('tenant').prefetch_related('issues').all()
        pending_requests = MaintenanceRequest.objects.filter(status='pending')

        for request_obj in maintenance_requests:
            user = request_obj.tenant
            if user:
                full_name = f"{user.first_name} {user.last_name}".strip()
                tenant_match = Tenant.objects.select_related('room_number').filter(full_name__iexact=full_name).first()

                if tenant_match:
                    issue_names = ", ".join([issue.name for issue in request_obj.issues.all()])
                    report_data.append({
                        'room_number': tenant_match.room_number.room_number,
                        'full_name': tenant_match.full_name,
                        'issue': issue_names or 'No issue listed',
                        'date_reported': request_obj.requested_at,
                        'status': request_obj.get_status_display(),
                    })

        if self.request.user.is_superuser:
            unread_messages_count = ChatMessage.objects.filter(
                receiver=self.request.user, is_read=False
            ).count()
        else:
            unread_messages_count = 0

        context.update({
            'total_sales_for_year': total_sales_for_year,
            'tenant_count': tenant_count,
            'total_unit': total_unit,
            'reports': report_data,
            'pending_requests': pending_requests,
            'unread_messages_count': unread_messages_count,
        })

        return context


def reports(request):
    report_data = []

    maintenance_requests = MaintenanceRequest.objects.select_related('tenant').prefetch_related('issues').all()

    for request_obj in maintenance_requests:
        user = request_obj.tenant
        if user:
            full_name = f"{user.first_name} {user.last_name}".strip()
            tenant_match = Tenant.objects.select_related('room_number').filter(full_name__iexact=full_name).first()

            if tenant_match:
                issue_names = ", ".join([issue.name for issue in request_obj.issues.all()])

                report_data.append({
                    'room_number': tenant_match.room_number.room_number,
                    'full_name': tenant_match.full_name,
                    'issue': issue_names or 'No issue listed',
                    'date_reported': request_obj.requested_at,
                    'status': request_obj.get_status_display(),
                })

    if request.user.is_superuser:
        unread_messages_count = ChatMessage.objects.filter(
            receiver=request.user, is_read=False
        ).count()
    else:
        unread_messages_count = 0

    context = {
        'reports': report_data,
        'unread_messages_count': unread_messages_count
    }

    return render(request, 'dashboard/reports.html', context)

def edit_report(request):
    if request.method == 'POST':
        # Process the form data and update the status for each report
        for key, value in request.POST.items():
            if key.startswith("status_"):  # Check for status_<report_id>
                report_id = key.split("_")[1]  # Extract the report ID from the name attribute (e.g., status_1 -> 1)
                
                if report_id.isdigit():  # Ensure the report ID is a valid number
                    try:
                        # Get the report by its ID
                        report = MaintenanceRequest.objects.get(id=report_id)
                        # Update the status of the report
                        report.status = value
                        report.save()  # Save the updated status
                    except MaintenanceRequest.DoesNotExist:
                        # If the report does not exist, you can choose to ignore or log it
                        pass
        
        # After processing the form, redirect back to the reports page
        return redirect('landlord:reports')  # This assumes you have a URL pattern named 'reports'

    # Retrieve the updated reports from the database
    report_data = []
    maintenance_requests = MaintenanceRequest.objects.select_related('tenant').prefetch_related('issues').all()

    for request_obj in maintenance_requests:
        user = request_obj.tenant
        if user:
            full_name = f"{user.first_name} {user.last_name}".strip()
            tenant_match = Tenant.objects.select_related('room_number').filter(full_name__iexact=full_name).first()

            if tenant_match:
                # Join issue names into a string
                issue_names = ", ".join([issue.name for issue in request_obj.issues.all()])

                report_data.append({
                    'room_number': tenant_match.room_number.room_number,
                    'full_name': tenant_match.full_name,
                    'issue': issue_names or 'No issue listed',
                    'date_reported': request_obj.requested_at,
                    'status': request_obj.get_status_display(),  # Use the human-readable status
                    'id': request_obj.id,  # Make sure to include the report's ID for form processing
                })

    # Pass the report data to the template
    context = {'reports': report_data}
    return render(request, 'dashboard/edit_report.html', context)

def payments(request):
    payments = Payment.objects.all().order_by('-date')
    return render(request, 'dashboard/payments.html', {'payments': payments})

class RoomListView(ListView):
    model = Room
    template_name = "dashboard/rooms.html"
    context_object_name = "rooms"

    def get_queryset(self):
        """Filter and sort the rooms based on query parameters."""
        room_filter = self.request.GET.get('filter', 'all')
        sort_by = self.request.GET.get('sort_by', 'room_number')

        rooms = Room.objects.all().order_by(sort_by)

        if room_filter == 'occupied':
            rooms = rooms.filter(availability='Occupied')
        elif room_filter == 'vacant':
            rooms = rooms.filter(availability='Vacant')

        return rooms

    def get_context_data(self, **kwargs):
        """Add additional context to the template."""
        context = super().get_context_data(**kwargs)

        context['room_filter'] = self.request.GET.get('filter', 'all')
        context['sort_by'] = self.request.GET.get('sort_by', 'room_number')
        context['count'] = context['rooms'].count() 
        context['all_count'] = Room.objects.count() 
        context['occupied_count'] = Room.objects.filter(availability='Occupied').count()
        context['vacant_count'] = Room.objects.filter(availability='Vacant').count()
        
        context['pending_requests'] = MaintenanceRequest.objects.filter(status='pending')

        return context
    
def tenants(request):
    tenants = Tenant.objects.all().order_by('room_number__room_number')
    return render(request, 'dashboard/tenants.html', {'tenants': tenants})

class TenantCreateView(CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'dashboard/add.html'
    success_url = reverse_lazy('landlord:tenants')
    
    def form_valid(self, form):
        room = form.cleaned_data['room_number']
        room.availability = 'Occupied'
        room.save()
        return super().form_valid(form)

def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)

    if request.method == 'POST':
        tenant.delete()
        return redirect('landlord:tenants')

    return render(request, 'dashboard/edit.html', {'tenant': tenant})
    
def sales(request):
    current_date = date.today()

    current_year = current_date.year

    start_of_first_half = date(current_year, 1, 1)
    end_of_first_half = date(current_year, 6, 30)

    start_of_second_half = date(current_year, 7, 1)
    end_of_second_half = date(current_year, 12, 31)

    total_revenue = Tenant.objects.filter(
        lease_start__lte=current_date, 
        end_date__gte=current_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0


    total_sales = 0


    if current_date <= end_of_first_half:
 
        total_sales = Tenant.objects.filter(
            lease_start__lte=end_of_first_half,
            end_date__gte=start_of_first_half
        ).aggregate(Sum('amount'))['amount__sum'] or 0
    elif current_date >= start_of_second_half:

        total_sales = Tenant.objects.filter(
            lease_start__lte=end_of_second_half,
            end_date__gte=start_of_second_half
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
    room_data = Room.objects.values('room_type').annotate(count=Count('room_type'))
    room_types = [entry['room_type'] for entry in room_data]
    room_counts = [entry['count'] for entry in room_data]
    
    paid_count = Payment.objects.filter(status__iexact='paid').count()
    overdue_count = Payment.objects.filter(status__iexact='overdue').count()

    return render(
        request, 
        'dashboard/sales.html', 
        {
            'total_revenue': total_revenue,
            'total_sales': total_sales,
            'room_types': json.dumps(room_types), 
            'room_counts': json.dumps(room_counts),
            'paid_count': paid_count,
            'overdue_count': overdue_count,
        }
    )


class AddRoomView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'dashboard/add_room.html'
    success_url = reverse_lazy('landlord:rooms')

    def form_valid(self, form):
        return super().form_valid(form)



def user_login(request):
    
    if request.user.is_authenticated:
        return redirect('landlord:main_dashboard')
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('main_dashboard')
            else:
                messages.error(request, "You are not authorized to access this portal.")
        else:
            messages.error(request, "Invalid username or password.")

    
    return render(request, 'dashboard/login.html')



def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)  
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                messages.error(request, "Username already taken.")
            else:
                user = form.save(commit=False)  
                user.set_password(form.cleaned_data["password"])
                user.save()
                messages.success(request, "Account created successfully!")
                return redirect("login")  
    else:
        form = SignupForm()

    return render(request, "dashboard/signup.html", {"form": form}) 


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('landlord:rooms')
    else:
        form = RoomForm(instance=room)

    return render(request, 'dashboard/edit_room.html', {'form': form})



@method_decorator(csrf_exempt, name='dispatch')
class RoomDeleteView(View):
    def post(self, request, room_id, *args, **kwargs):
        room = get_object_or_404(Room, id=room_id)

        if room.availability.lower() == "occupied":
            messages.error(request, "Occupied rooms cannot be deleted.")
            return redirect("landlord:rooms") 

        room.delete()
        messages.success(request, "Room deleted successfully.")
        return redirect("landlord:rooms")

def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('rooms')
    else:
        form = ImageUploadForm()

    return render(request, 'edit_room.html', {'form': form})

@method_decorator(csrf_exempt, name='dispatch')
class LandlordChatView(View):
    template_name = 'dashboard/message.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        tenants = User.objects.filter(is_superuser=False)

        for tenant in tenants:
            tenant.unread_messages_count = ChatMessage.objects.filter(
                sender=tenant,
                receiver=user,
                is_read=False
            ).count()

        selected_tenant_id = kwargs.get('user_id')
        selected_tenant = None
        messages = []
        room_number = None

        if selected_tenant_id:
            selected_tenant = get_object_or_404(User, id=selected_tenant_id, is_superuser=False)
            messages = ChatMessage.objects.filter(
                Q(sender=user, receiver=selected_tenant) |
                Q(sender=selected_tenant, receiver=user)
            ).order_by('timestamp')

            ChatMessage.objects.filter(
                sender=selected_tenant,
                receiver=user,
                is_read=False
            ).update(is_read=True)

            full_name = f"{selected_tenant.first_name} {selected_tenant.last_name}".strip()
            try:
                tenant_record = Tenant.objects.get(full_name__iexact=full_name)
                room_number = tenant_record.room_number.room_number
            except Tenant.DoesNotExist:
                room_number = None

        context = {
            'user': user,
            'tenants': tenants,
            'selected_tenant': selected_tenant,
            'messages': messages,
            'websocket_url': f"/ws/chat/{user.id}/",
            'room_number': room_number,
        }
        return render(request, self.template_name, context)


def send_receipt_email(payment):
    recipient_email = payment.tenant.user.email

    subject = f"Receipt for Payment {payment.reference_number}"
    html_message = render_to_string('dashboard/email_reciept.html', {'payment': payment})
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        'from@example.com',
        [recipient_email],
        fail_silently=False,
        html_message=html_message,
    )

def add_payment(request):
    if request.method == 'POST':
        room_number = request.POST.get('room_number')

        try:
            tenant = Tenant.objects.get(room_number=room_number)
        except Tenant.DoesNotExist:
            messages.error(request, f"Tenant with room number {room_number} does not exist.")
            return redirect('landlord:add_payment')

        amount = request.POST.get('amount')
        date = request.POST.get('date')
        status = request.POST.get('status')

        reference_number = generate_reference_number()

        payment = Payment(
            tenant=tenant,
            user=request.user,
            amount=amount,
            date=date,
            status=status,
            reference_number=reference_number
        )
        payment.save()

        send_receipt_email(payment)

        return redirect('landlord:payments')

    tenants = Tenant.objects.all()
    return render(request, 'dashboard/addpayment.html', {'tenants': tenants})

def generate_reference_number():
    """Generate a unique reference number."""
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PAY-{year}-{random_str}"
