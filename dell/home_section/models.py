from django.db import models

class IconTitle(models.Model):
    icon = models.ImageField(upload_to="icons/", null=True, blank=True)
    title = models.CharField(max_length=255)
    number = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Title обновляется автоматически
        self.title = f"{self.title.split(' (')[0]} ({self.number})"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
