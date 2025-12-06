from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe

class IndustryArticle(models.Model):
    title = models.CharField("Заголовок", max_length=200, default="Sanoat Rivoji")
    subtitle = models.CharField("Подзаголовок", max_length=200, blank=True, default="Yangi")
    content = models.TextField("Содержимое", help_text="Основной текст статьи")
    year = models.PositiveIntegerField("Год", default=2025)
    statistic = models.CharField("Статистика (текст)", max_length=100, blank=True, default="+12% o‘sish")
    image = models.ImageField("Rasm", upload_to="industry_images/", blank=True, null=True)
    created_at = models.DateTimeField("Создано", default=timezone.now)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Статья о промышленности"
        verbose_name_plural = "Статьи о промышленности"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.year})"

    def image_tag(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" style="max-height:120px;"/>')
        return "(Нет изображения)"
    image_tag.short_description = "Превью"
    image_tag.allow_tags = True
