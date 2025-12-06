from django.db import models

class Feature(models.Model):
    title = models.CharField(max_length=255)
    desc = models.TextField()
    icon = models.ImageField(upload_to='feature_icons/')  # фото

    def __str__(self):
        return self.title
