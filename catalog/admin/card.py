from django.contrib import admin
from nested_admin import NestedModelAdmin, NestedTabularInline, NestedStackedInline
from ..models import (
    CardVariant,
    Card,
    CardPrinting,
    LocalizedCard,
    LocalizedAttack,
    AttackCost,
    Attack,
    LocalizedAbility,
    Ability,
)
import json


class LocalizedAttackInline(NestedTabularInline):
    model = LocalizedAttack
    extra = 1


class AttackCostInline(NestedTabularInline):
    model = AttackCost
    extra = 1


class AttackInline(NestedTabularInline):
    model = Attack
    extra = 1
    inlines = [AttackCostInline, LocalizedAttackInline]


class LocalizedAbilityInline(NestedTabularInline):
    model = LocalizedAbility
    extra = 1


class AbilityInline(NestedStackedInline):
    model = Ability
    extra = 1
    inlines = [LocalizedAbilityInline]
    readonly_fields = ("id",)
    fields = ("id",)


class LocalizedCardInline(NestedTabularInline):
    model = LocalizedCard
    extra = 1
    fields = ("language", "name", "number", "total_cards_override", "description")
    verbose_name = "Translation and Numbering"
    verbose_name_plural = "Translations and Numberings"


class CardPrintingInline(NestedTabularInline):
    model = CardPrinting
    extra = 1
    inlines = [LocalizedCardInline]
    fields = ("expansion", "variant", "rarity", "master_image")
    verbose_name = "Printing variation"
    verbose_name_plural = "Printing variations"


@admin.register(Card)
class CardAdmin(NestedModelAdmin):
    list_display = ("internal_name", "get_expansions", "supertype", "subtype", "hp")
    list_filter = ("printings__expansion", "supertype", "subtype", "types")
    search_fields = (
        "internal_name",
        "printings__localizations__name",
        "slug",
    )
    prepopulated_fields = {"slug": ("internal_name",)}

    inlines = [AbilityInline, AttackInline, CardPrintingInline]

    def get_expansions(self, instance):
        codes = instance.printings.values_list("expansion__code", flat=True).distinct()
        return ", ".join(codes) if codes else "No expansions"

    get_expansions.short_description = "Expansions"

    fieldsets = (
        (
            "General information",
            {
                "fields": (
                    "internal_name",
                    "slug",
                    "supertype",
                    "subtype",
                    "hp",
                    "retreat_cost",
                )
            },
        ),
        ("Types and energy", {"fields": ("types", "energy_value")}),
        (
            "Weakness & Resistance",
            {
                "fields": (
                    ("weak_type", "weak_value"),
                    ("resist_type", "resist_value"),
                )
            },
        ),
    )

    class Media:
        js = ("js/card_field_toggles.js",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        constants = {
            "POKEMON": Card.SuperType.POKEMON.value,
            "ENERGY": Card.SuperType.ENERGY.value,
            "TRAINER": Card.SuperType.TRAINER.value,
        }
        if "supertype" in form.base_fields:
            form.base_fields["supertype"].widget.attrs["data-supertypes"] = json.dumps(
                constants
            )
        return form


@admin.register(CardVariant)
class CardVariantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
