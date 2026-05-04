from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Notification, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "is_super_admin", "is_staff", "is_active", "date_joined"]
    list_editable = ["is_super_admin", "is_staff"]
    list_filter = ["is_super_admin", "is_staff", "is_active"]
    search_fields = ["email", "username"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Paddox", {"fields": ("avatar_url", "is_super_admin")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Paddox", {"fields": ("email", "avatar_url", "is_super_admin")}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "title", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    search_fields = ["user__email", "title"]
    readonly_fields = ["created_at"]
