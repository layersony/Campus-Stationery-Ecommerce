from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Address
from datetime import datetime

def get_year_choices():
    current_year = datetime.now().year
    return [(year, year) for year in range(current_year - 5, current_year + 6)]

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    student_id = forms.CharField(required=True, max_length=20)
    phone_number = forms.CharField(required=True, max_length=15)
    course = forms.CharField(required=True, max_length=100)
    
    year_of_study = forms.ChoiceField(
        choices=get_year_choices,
        initial=datetime.now().year,
        required=True,
        help_text="Select your year of study"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'student_id', 
                  'phone_number', 'course', 'year_of_study', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.student_id = self.cleaned_data['student_id']
        user.phone_number = self.cleaned_data['phone_number']
        user.course = self.cleaned_data['course']
        user.year_of_study = int(self.cleaned_data['year_of_study'])
        if commit:
            user.save()
        return user


class VendorRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    business_name = forms.CharField(required=True, max_length=200)
    business_registration = forms.CharField(required=True, max_length=50)
    phone_number = forms.CharField(required=True, max_length=15)
    location = forms.CharField(required=True, max_length=200)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'business_name',
                  'business_registration', 'phone_number', 'location', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'vendor'
        user.business_name = self.cleaned_data['business_name']
        user.business_registration = self.cleaned_data['business_registration']
        user.phone_number = self.cleaned_data['phone_number']
        user.location = self.cleaned_data['location']
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['name', 'phone', 'hostel_block', 'room_number', 'campus_building', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'hostel_block': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Block A'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101'}),
            'campus_building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Library Building'}),
        }

class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['phone_number'].help_text = "Format: +254712345678 or 0712345678"
        self.fields['profile_picture'].help_text = "Upload a profile image (optional)"