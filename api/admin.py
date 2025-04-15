from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django_apscheduler.models import DjangoJob, DjangoJobExecution

from api import models


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "is_superuser",
                    "role",
                    "teams",
                )
            },
        ),
    )


@admin.register(models.OrgVerdict)
class OrgVerdictAdmin(admin.ModelAdmin):
    list_display = ("org", "solution", "points")

    def has_add_permission(self, request):
        return False


admin.site.unregister(Group)
admin.site.unregister(DjangoJob)
admin.site.unregister(DjangoJobExecution)
