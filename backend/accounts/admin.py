from django.contrib import admin

from .models import Address, CustomUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"


class AddressInline(admin.StackedInline):
    model = Address
    can_delete = False
    verbose_name_plural = "Addresses"


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone_number", "is_staff", "is_active")
    search_fields = ("email", "phone_number")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)
    inlines = [ProfileInline, AddressInline]
    title = "Custom User Administration"
