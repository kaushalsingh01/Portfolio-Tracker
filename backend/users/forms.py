from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users.models import CustomUser
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name", "last_name", "email", "date_of_birth",
            "is_staff", "is_active", "groups", "user_permissions"
        ]

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name", "last_name", "email", "date_of_birth",
            "is_staff", "is_active", "groups", "user_permissions"
        ]