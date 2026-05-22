from django.db import models
from django.utils.text import slugify
from .expansion import Expansion
from .energy_type import EnergyType
from shared.aws import aws_client
from shared.messaging import ImageTask
from shared.domain import CardIdentity, SupportedLanguage

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

    raw_image = models.ImageField(upload_to="cards/raw/", null=True, blank=True)
    master_image_path = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        image_changed = False

        if not is_new:
            old_instance = LocalizedCard.objects.get(pk=self.pk)
            if old_instance.raw_image != self.raw_image:
                image_changed = True
        
        super().save(*args, **kwargs)

        if self.raw_image and (is_new or image_changed):
            self._send_processing_task()

    def _send_processing_task(self):
        card_identity = CardIdentity(
            expansion=self.printing.expansion.code,
            lang=self.language,
            id=str(self.id)
        )

        relative_path = self.raw_image.name
        storage_location = getattr(self.raw_image.storage, "location", "")

        # Resilient for hypothetical location removal, wont generate a s3 key starting with '/'
        if storage_location:
            absolute_s3_key = f"{storage_location.strip("/")}/{relative_path}"
        else:
            absolute_s3_key = relative_path

        print("ABSOLUTE",absolute_s3_key)

        task = ImageTask(
            card=card_identity,
            s3_key = absolute_s3_key
        )

        aws_client.trigger_image_processing(task)

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
