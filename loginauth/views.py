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
    template_name = 'loginauth/login.html'  # Your login template path

    def form_valid(self, form):
        """Login the user and trigger OTP generation for email"""
        user = form.get_user()

        if user.is_authenticated:
            # Log the user in
            login(self.request, user)

            # Create or retrieve the EmailDevice associated with the user
            device, created = EmailDevice.objects.get_or_create(user=user)

            # Generate the OTP challenge (this triggers email sending)
            device.generate_challenge()

            # Now redirect to OTP verification page
            return redirect(reverse('email_otp'))  # Ensure OTP page is being routed correctly

        else:
            # If the user is not authenticated, return to login page
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

        # Retrieve the device from the session (the device is tied to the user)
        try:
            device = EmailDevice.objects.get(user=request.user)
        except EmailDevice.DoesNotExist:
            # If device does not exist, redirect to login or handle the error
            return redirect('login')

        # Check if the OTP entered matches the generated one
        if device.verify_token(entered_otp):
            # OTP is correct, log the user in and redirect to their dashboard
            login(request, request.user)

            # Redirect to the appropriate dashboard
            return redirect('landlord:main_dashboard') if request.user.is_superuser else redirect('tenant:dashboard')
        else:
            # OTP is incorrect, show an error message
            return render(request, 'loginauth/email_otp.html', {'error': 'Invalid OTP. Please try again.'})

    return render(request, 'loginauth/email_otp.html')

@login_required
def resend_otp(request):
    try:
        device = EmailDevice.objects.get(user=request.user)
        device.generate_challenge()  # Triggers a new OTP email
        messages.success(request, "A new OTP has been sent to your email.")
    except EmailDevice.DoesNotExist:
        messages.error(request, "No OTP device found. Please log in again.")
        return redirect('login')

    return redirect('email_otp')

def signUp(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        
        if form.is_valid():
            # Create the User
            user = form.save()

            # Extract first and last name from the form to match with Tenant's full_name
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')

            # Search for the Tenant whose full name matches
            tenants = Tenant.objects.all()  # This could be optimized to match by full name directly

            matched_tenant = None
            for tenant in tenants:
                tenant_full_name = tenant.full_name.strip().split()

                if len(tenant_full_name) >= 2:
                    tenant_first_name = ' '.join(tenant_full_name[:-1])  # Everything except the last part
                    tenant_last_name = tenant_full_name[-1]  # The last part as last name

                    if (first_name.lower() == tenant_first_name.lower() and
                            last_name.lower() == tenant_last_name.lower()):
                        matched_tenant = tenant
                        break  # Stop once a match is found
            
            if matched_tenant:
                # If a matching tenant is found, link the tenant to the user
                matched_tenant.user = user
                matched_tenant.save()  # Save the tenant with the user association

            # Optionally, create a user profile (if you have that model)
            user_profile = UserProfile.objects.create(
                user=user,
                terms_accepted=True,
                date_accepted=timezone.now()
            )

            # Log the user in and show a success message
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect('login')
        
        else:
            # Print the form errors to debug
            print(form.errors)
            messages.error(request, "There were errors in your form. Please fix them.")
            return render(request, 'loginauth/signup.html', {'form': form})

    else:
        form = SignUpForm()
        return render(request, 'loginauth/signup.html', {'form': form})