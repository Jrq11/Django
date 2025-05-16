from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm
from .models import UserProfile
from django.utils import timezone
import time
from dashboard.models import Tenant
from django_otp.plugins.otp_email.models import EmailDevice

class CustomLoginView(LoginView):
    template_name = 'loginauth/login.html'

    def form_valid(self, form):
        """Login the user and trigger OTP generation for email"""
        user = form.get_user()

        if user.is_authenticated:
            login(self.request, user)

            device, created = EmailDevice.objects.get_or_create(user=user)

            device.generate_challenge()

            return redirect(reverse('email_otp'))

        else:

            return redirect('login')

    def form_invalid(self, form):
        """Handle invalid login attempts"""
        response = super().form_invalid(form)
        if 'username' in form.errors or 'password' in form.errors:
            form.add_error(None, 'Invalid username or password. Please try again.')
        return response
    
@login_required
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp_combined')

        try:
            device = EmailDevice.objects.get(user=request.user)
        except EmailDevice.DoesNotExist:
            return redirect('login')

        if device.verify_token(entered_otp):
            login(request, request.user)

            return redirect('landlord:main_dashboard') if request.user.is_superuser else redirect('tenant:dashboard')
        else:
            return render(request, 'loginauth/email_otp.html', {'error': 'Invalid OTP. Please try again.'})

    return render(request, 'loginauth/email_otp.html')

@login_required
def resend_otp(request):
    try:
        device = EmailDevice.objects.get(user=request.user)
        device.generate_challenge()
        messages.success(request, "A new OTP has been sent to your email.")
    except EmailDevice.DoesNotExist:
        messages.error(request, "No OTP device found. Please log in again.")
        return redirect('login')

    return redirect('email_otp')

def signUp(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        
        if form.is_valid():
            user = form.save()

            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')

            tenants = Tenant.objects.all()

            matched_tenant = None
            for tenant in tenants:
                tenant_full_name = tenant.full_name.strip().split()

                if len(tenant_full_name) >= 2:
                    tenant_first_name = ' '.join(tenant_full_name[:-1])
                    tenant_last_name = tenant_full_name[-1]

                    if (first_name.lower() == tenant_first_name.lower() and
                            last_name.lower() == tenant_last_name.lower()):
                        matched_tenant = tenant
                        break 
            
            if matched_tenant:
                matched_tenant.user = user
                matched_tenant.save()

            user_profile = UserProfile.objects.create(
                user=user,
                terms_accepted=True,
                date_accepted=timezone.now()
            )
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect('login')
        
        else:
            print(form.errors)
            messages.error(request, "There were errors in your form. Please fix them.")
            return render(request, 'loginauth/signup.html', {'form': form})

    else:
        form = SignUpForm()
        return render(request, 'loginauth/signup.html', {'form': form})