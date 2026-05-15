from django.db import models
from aws_shared.languages import SupportedLanguage
from django.utils.text import slugify


class EnergyType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    color_code = models.CharField(max_length=7, blank=True)
    icon = models.ImageField(upload_to="energies/icons", null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code.upper()


class LocalizedEnergyType(models.Model):
    energy_type = models.ForeignKey(
        EnergyType, on_delete=models.CASCADE, related_name="localizations"
    )
    language = models.CharField(max_length=2, choices=SupportedLanguage.to_choices())
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ("energy_type", "language")
