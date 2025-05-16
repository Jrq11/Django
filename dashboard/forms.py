from django import forms
from .models import UploadedImage, Room, Tenant, Payment
from django.contrib.auth.models import User

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedImage
        fields = ['image']
        
class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "password"]
        widgets = {
            "password" : forms.PasswordInput(),
        }
        
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'capacity', 'availability', 'description']
        
class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['room_number', 'full_name', 'amount', 'lease_start', 'end_date', 'emergency_contact']
        widgets = {
            'lease_start': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['room_number'].queryset = Room.objects.filter(availability='Occupied').order_by('room_number')
            self.fields['room_number'].initial = self.instance.room_number
            self.fields['room_number'].required = False
        else:
            self.fields['room_number'].queryset = Room.objects.filter(availability='Vacant').order_by('room_number')
            self.fields['room_number'].required = True

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'amount', 'date', 'status', 'reference_number']

    tenant = forms.ModelChoiceField(queryset=None, widget=forms.HiddenInput(), required=False)