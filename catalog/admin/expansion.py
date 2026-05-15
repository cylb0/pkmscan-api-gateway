from django.contrib import admin
from ..models import Expansion, LocalizedExpansion


class LocalizedExpansionInline(admin.StackedInline):
    model = LocalizedExpansion
    extra = 1


@admin.register(Expansion)
class ExpansionAdmin(admin.ModelAdmin):
    list_display = ("code", "slug")
    inlines = [LocalizedExpansionInline]
    prepopulated_fields = {"slug": ("code",)}
