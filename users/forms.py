from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with reCAPTCHA"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'captcha')


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False, disabled=True)  # Email cannot be changed
    
    class Meta:
        model = UserProfile
        fields = ['profile_photo', 'bio', 'sex', 'education_level', 'department']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
