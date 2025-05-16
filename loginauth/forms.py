from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from dashboard.models import Tenant

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    terms_and_conditions = forms.BooleanField(required=True, label="I agree to the Terms and Conditions")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()

        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
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
            else:
                self.add_error('first_name', 'Tenant full name is incomplete.')

        if not matched_tenant:
            self.add_error('first_name', 'First name does not match any tenant record.')
            self.add_error('last_name', 'Last name does not match any tenant record.')

        if not cleaned_data.get('terms_and_conditions'):
            self.add_error('terms_and_conditions', 'You must agree to the terms and conditions.')

        return cleaned_data