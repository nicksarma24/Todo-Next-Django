from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "auth0_user_id", "created_at")
    search_fields = ("email", "auth0_user_id")
