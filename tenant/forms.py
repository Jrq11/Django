from django import forms
from .models import MaintenanceRequest, Location, IssueType, UserProfile

class MaintenanceRequestForm(forms.ModelForm):
    locations = forms.ModelMultipleChoiceField(
        queryset=Location.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    issues = forms.ModelMultipleChoiceField(
        queryset=IssueType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = MaintenanceRequest
        fields = ['locations', 'issues', 'description']
   
   
        
class UserProfileForm(forms.ModelForm):
    
    guardian_email = forms.CharField(required=False)
        
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'middle_name', 'last_name', 'birthday',
            'gender', 'phone_no', 'address', 'email',
            'guardian_name', 'guardian_phone_no', 'guardian_address', 'guardian_email'
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.TextInput(),  # changed from Textarea to fit your layout
            'guardian_address': forms.TextInput(),  # same here
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False  # make all fields optional