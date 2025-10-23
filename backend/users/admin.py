from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.forms import CustomUserChangeForm, CustomUserCreationForm
from users.models import CustomUser

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = (
        "email", "first_name", "last_name", "date_of_birth",
        "is_staff", "is_active"
    )
    list_filter = ("is_staff", "is_active", "groups")

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("date_of_birth",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("date_of_birth",)}),
    )

    search_fields = ("email",)
    ordering = ("email",)

admin.site.register(CustomUser, CustomUserAdmin)