from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth.models import User
from dashboard.models import ChatMessage, Tenant, Payment
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import MaintenanceRequestForm, UserProfileForm
from .models import Location, IssueType, MaintenanceRequest

@method_decorator(login_required, name='dispatch')
class TenantDashboardView(TemplateView):
    template_name = "tenant/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logged_in_user = self.request.user

        logged_in_user_full_name = f"{logged_in_user.first_name} {logged_in_user.last_name}".strip().lower()

        tenant = Tenant.objects.filter(full_name__iexact=logged_in_user_full_name).first()

        if tenant:
            print(f"Tenant found: {tenant.full_name}, Amount: {tenant.amount}")
        else:
            print("No tenant found matching the user's full name")

        tenant_requests = MaintenanceRequest.objects.filter(tenant=logged_in_user).order_by('-requested_at')

        unread_messages_count = ChatMessage.objects.filter(
            receiver=logged_in_user, is_read=False
        ).count()

        context['tenant'] = tenant
        context['requests'] = tenant_requests
        context['unread_messages_count'] = unread_messages_count

        return context


@login_required
def profile(request):
    user_profile = request.user.tenant_profile

    tenant = Tenant.objects.filter(user=request.user).first()

    unread_messages_count = ChatMessage.objects.filter(
        receiver=request.user, is_read=False
    ).count()

    return render(request, 'tenant/profile.html', {
        'user_profile': user_profile,
        'tenant': tenant,
        'unread_messages_count': unread_messages_count
    })

@login_required
def edit_profile(request):
    user_profile = request.user.tenant_profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('tenant:profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'tenant/edit_profile.html', {
        'form': form,
        'user_profile': user_profile,
    })

@login_required
def payment(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
        payments = Payment.objects.filter(tenant=tenant)
    except Tenant.DoesNotExist:
        tenant = None
        payments = []

    unread_messages_count = ChatMessage.objects.filter(
        receiver=request.user, is_read=False
    ).count()

    context = {
        'tenant': tenant,
        'payments': payments,
        'unread_messages_count': unread_messages_count,
    }
    return render(request, 'tenant/payment.html', context)

@login_required
def maintenance(request):
    maintenance_requests = MaintenanceRequest.objects.filter(tenant=request.user).order_by

    unread_messages_count = ChatMessage.objects.filter(
        receiver=request.user, is_read=False
    ).count()

    context = {
        'maintenance_requests': maintenance_requests,
        'unread_messages_count': unread_messages_count,
    }
    return render(request, 'tenant/maintenance.html', context)

@login_required
def maintenance_req(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)

        if form.is_valid():
            selected_locations = form.cleaned_data['locations']
            selected_issue_types = form.cleaned_data['issues']

            location_ids = list(selected_locations.values_list('id', flat=True))
            issue_type_ids = list(selected_issue_types.values_list('id', flat=True))

            request.session['maintenance_data'] = {
                'location_ids': location_ids,
                'issues_ids': issue_type_ids,
                'description': form.cleaned_data['description'],
            }

            return redirect('tenant:review_request')
    
    else:
        form = MaintenanceRequestForm()

    return render(request, 'tenant/maintenance_request.html', {'form': form})



@login_required
def review_request(request):
    maintenance_data = request.session.get('maintenance_data', None)

    if not maintenance_data:
        return redirect('tenant:dashboard')

    locations = Location.objects.filter(id__in=maintenance_data['location_ids'])
    issues = IssueType.objects.filter(id__in=maintenance_data['issues_ids'])

    current_time = timezone.localtime(timezone.now()).strftime('%I:%M %p')

    if request.method == 'POST':
        maintenance_request = MaintenanceRequest.objects.create(
            tenant=request.user,
            description=maintenance_data['description']
        )
        
        maintenance_request.locations.set(locations)
        maintenance_request.issues.set(issues)

        del request.session['maintenance_data']

        return redirect('tenant:maintenance')

    context = {
        'locations': locations,
        'issues': issues,
        'description': maintenance_data['description'],
        'current_time': current_time
    }

    return render(request, 'tenant/review_request.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

@method_decorator(csrf_exempt, name='dispatch')
class TenantChatView(LoginRequiredMixin, View):
    template_name = 'tenant/message.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return redirect('some_other_view')

        landlord = User.objects.filter(is_superuser=True).first()

        if landlord:
            landlord.unread_messages_count = ChatMessage.objects.filter(
                sender=landlord,
                receiver=user,
                is_read=False
            ).count()

        messages = []
        if landlord:
            messages = ChatMessage.objects.filter(
                Q(sender=user, receiver=landlord) | 
                Q(sender=landlord, receiver=user)
            ).order_by('timestamp')

            ChatMessage.objects.filter(
                sender=landlord,
                receiver=user,
                is_read=False
            ).update(is_read=True)

        context = {
            'user': user,
            'selected_tenant': landlord,
            'messages': messages,
            'websocket_url': f"/ws/chat/{user.id}/",
            'unread_messages_count': landlord.unread_messages_count if landlord else 0,
        }

        return render(request, self.template_name, context)
    
def my_view(request):
    current_time = timezone.now().strftime("%I:%M %p")
    return render(request, 'my_template.html', {'current_time': current_time})
