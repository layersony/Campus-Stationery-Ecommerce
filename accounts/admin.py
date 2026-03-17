from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # what shows in list view
    list_display = ("email", "username", "user_type", "is_staff", "is_active")
    list_filter = ("user_type", "is_staff", "is_active")

    # search
    search_fields = ("email", "username")
    ordering = ("-created_at",)

    # fields layout
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number", "profile_picture")}),
        ("Roles", {"fields": ("user_type", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Status", {"fields": ("is_active", "is_verified")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
        
        ("Student Info", {"fields": ("student_id", "course", "year_of_study")}),
        ("Vendor Info", {"fields": ("business_name", "business_registration", "location")}),
    )

    # fields when creating user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "user_type"),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "phone", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("name", "phone", "user__email")