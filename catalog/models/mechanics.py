from django.db import models
from .card import Card
from .energy_type import EnergyType
from aws_shared.languages import SupportedLanguage


class Attack(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="attacks")
    damage = models.CharField(max_length=10, blank=True)
    cost_types = models.ManyToManyField(
        EnergyType, through="AttackCost", related_name="attacks"
    )

    def __str__(self):
        loc = self.localizations.filter(language=SupportedLanguage.EN).first()
        name = loc.name if loc else "Unknown"
        return f"Attack: {name} - ({self.card.slug})"


class AttackCost(models.Model):
    attack = models.ForeignKey(Attack, on_delete=models.CASCADE, related_name="costs")
    energy_type = models.ForeignKey(EnergyType, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("attack", "energy_type")

    def __str__(self):
        return f"{self.quantity}x {self.energy_type}"


class LocalizedAttack(models.Model):
    attack = models.ForeignKey(
        Attack, on_delete=models.CASCADE, related_name="localizations"
    )
    language = models.CharField(max_length=2, choices=SupportedLanguage.to_choices())
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("attack", "language")


class Ability(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="abilities")

    class Meta:
        verbose_name_plural = "Abilities"

    def __str__(self):
        loc = self.localizations.filter(language=SupportedLanguage.EN).first()
        name = loc.name if loc else "Unknown"
        return f"Ability: {name} - {self.card}"


class LocalizedAbility(models.Model):
    ability = models.ForeignKey(
        Ability, on_delete=models.CASCADE, related_name="localizations"
    )
    language = models.CharField(max_length=2, choices=SupportedLanguage.to_choices())
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "LocalizedAbilities"
        unique_together = ("ability", "language")
