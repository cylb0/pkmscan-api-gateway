from django.contrib import admin
from ..models import EnergyType, LocalizedEnergyType


class LocalizedEnergyTypeInline(admin.StackedInline):
    model = LocalizedEnergyType
    extra = 1


@admin.register(EnergyType)
class EnergyTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "slug", "color_code", "icon")
    inlines = [LocalizedEnergyTypeInline]
    prepopulated_fields = {"slug": ("code",)}
