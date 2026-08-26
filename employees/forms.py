from django import forms
from .models import Employee, Attendance

class EmployeeForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False, help_text='Optional. If provided, a login account will be created.')
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text='Optional. Leave blank if no login account is needed.')
    
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'phone', 'age', 'department', 'designation', 'salary', 'join_date', 'profile_picture', 'is_active']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No extra classes for default UI

class AttendanceForm(forms.ModelForm):
    check_in_photo_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Attendance
        fields = ['employee', 'check_in_photo_data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No extra classes for default UI
