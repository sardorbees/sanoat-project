from django.db import models

class Application(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Полное имя")
    email = models.EmailField(max_length=255, verbose_name="Email", blank=True, null=True)
    phone_number = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    question = models.TextField(verbose_name="Вопрос")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.full_name} — {self.phone_number or self.email}"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
