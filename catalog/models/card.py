from django.db import models
from django.utils.text import slugify
from .expansion import Expansion
from .energy_type import EnergyType
from aws_shared.languages import SupportedLanguage


class CardVariant(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=50, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Card(models.Model):
    class SuperType(models.TextChoices):
        POKEMON = "pokemon", "Pokemon"
        TRAINER = "trainer", "Trainer"
        ENERGY = "energy", "Energy"

    class SubType(models.TextChoices):
        BASIC = "basic", "Basic"
        STAGE_1 = "stage-1", "Stage 1"
        STAGE_2 = "stage-2", "Stage 2"

        BASIC_ENERGY = "basic-energy", "Basic Energy"
        SPECIAL_ENERGY = "special-energy", "Special Energy"

        ITEM = "item", "Item"
        SUPPORTER = "supporter", "Supporter"
        STADIUM = "stadium", "Stadium"
        SPECIAL = "special", "Special"

    internal_name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    supertype = models.CharField(
        max_length=20, choices=SuperType.choices, default=SuperType.POKEMON
    )
    subtype = models.CharField(max_length=20, choices=SubType.choices, blank=True)
    hp = models.IntegerField(null=True, blank=True)
    retreat_cost = models.IntegerField(default=0)

    types = models.ManyToManyField(EnergyType, related_name="cards", blank=True)
    energy_value = models.PositiveIntegerField(
        null=True, blank=True, help_text="Face value of the energy type"
    )

    weak_type = models.ForeignKey(
        EnergyType,
        on_delete=models.PROTECT,
        related_name="cards_with_weakness",
        blank=True,
        null=True,
    )
    weak_value = models.CharField(max_length=10, blank=True, help_text="e.g. x2, +20")
    resist_type = models.ForeignKey(
        EnergyType,
        on_delete=models.PROTECT,
        related_name="cards_with_resistance",
        blank=True,
        null=True,
    )
    resist_value = models.CharField(max_length=10, blank=True, help_text="e.g. -20")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.internal_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.internal_name


class CardPrinting(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="printings")
    variant = models.ForeignKey(
        CardVariant, on_delete=models.PROTECT, related_name="printings"
    )
    expansion = models.ForeignKey(
        Expansion, on_delete=models.CASCADE, related_name="cards"
    )
    rarity = models.CharField(max_length=50)
    master_image = models.ImageField(upload_to="cards/master/", null=True, blank=True)

    def __str__(self):
        return f"{self.card} - {self.variant.name}"


class LocalizedCard(models.Model):
    printing = models.ForeignKey(
        CardPrinting, on_delete=models.CASCADE, related_name="localizations"
    )
    language = models.CharField(
        max_length=2,
        choices=SupportedLanguage.to_choices(),
        default=SupportedLanguage.EN,
    )
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=10, help_text="e.g. 'H28', '40'")
    total_cards_override = models.IntegerField(
        null=True,
        blank=True,
        help_text="Specific total for a group (e.g. 32 for Aquapolis Holos)",
    )
    description = models.TextField(blank=True, null=True)

    @property
    def hp(self):
        return self.printing.card.hp

    @property
    def expansion(self):
        return self.printing.expansion

    @property
    def variant_name(self):
        return self.printing.variant

    @property
    def full_number(self):
        total = self.total_cards_override or self.printing.expansion.total_cards
        return f"{self.number}/{total}"

    @property
    def image(self):
        return self.printing.master_image

    class Meta:
        unique_together = ("printing", "language")

    def __str__(self):
        return f"{self.name} ({self.number}) - {self.language.upper()}"
