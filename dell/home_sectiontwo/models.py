from django.db import models

class Info(models.Model):
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)
    base_title = models.CharField(max_length=255)
    title = models.CharField(max_length=255, editable=False)
    number = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # авто-обновление title при изменении number
        self.title = f"{self.base_title} ({self.number})"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
