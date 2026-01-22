from django.db import models
import uuid

# -------------------------------
# Баннеры на главной странице
# -------------------------------
class Banner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_url = models.URLField()
    action_link = models.CharField(
        max_length=255,
        help_text='Ссылка для действия, например: "begab://club/123"'
    )
    priority = models.IntegerField(default=0, help_text='Чем выше число — тем выше приоритет')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"Banner {self.id} - {self.action_link}"


# -------------------------------
# Клубы
# -------------------------------
class Club(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    logo_url = models.URLField(blank=True, null=True)
    rating = models.FloatField(default=0, help_text='Средний рейтинг клуба (кешированный)')

    def __str__(self):
        return self.name
