from django.contrib import admin
from .models import User, LoginHistory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'success')
    list_filter = ('success', 'login_time')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-login_time',)
