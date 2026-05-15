from django.db import models
from django.utils.text import slugify
from aws_shared.languages import SupportedLanguage


class Expansion(models.Model):
    code = models.CharField(max_length=5, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class LocalizedExpansion(models.Model):
    expansion = models.ForeignKey(
        Expansion, on_delete=models.CASCADE, related_name="localizations"
    )
    language = models.CharField(max_length=2, choices=SupportedLanguage.to_choices())
    name = models.CharField(max_length=100)
    release_date = models.DateField(null=True, blank=True)
    total_cards = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("expansion", "language")

    def __str__(self):
        return f"{self.name} ({self.language.upper()})"
