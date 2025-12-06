from django.db import models

from django_ckeditor_5.fields import CKEditor5Field


class ArticleTag(models.Model):
    title = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Медиа теги'
        verbose_name_plural = 'Медиа теги'


class Article(models.Model):
    class DifficultyChoices(models.TextChoices):
        easy = 'Easy'
        medium = 'Medium'
        hard = 'Hard'
        impossible = 'Impossible'

    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DifficultyChoices.choices)
    reading_time = models.IntegerField()
    views = models.IntegerField(default=0)
    card_desc = models.TextField(default=" ")
    description = CKEditor5Field()
    image = models.ImageField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(to=ArticleTag, related_name='tags')
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


    class Meta:
        verbose_name = 'Медиа статъя'
        verbose_name_plural = 'Медиа статъя'
