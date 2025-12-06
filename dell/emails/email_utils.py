from django.core.mail import EmailMultiAlternatives


def send_password_verify_code(email, code):
    subject = "Подтверждение смены пароля"
    from_email = "no-reply@example.com"

    text_content = f"Ваш код подтверждения: {code}"

    html_content = f"""
    <html>
    <body style="font-family: Arial; background:#f2f2f2; padding:20px;">
      <div style="max-width:600px;margin:auto;background:white;padding:25px;border-radius:10px;">
        <h2 style="color:#333;">Подтверждение смены пароля</h2>
        <p>Введите этот код, чтобы завершить изменение пароля:</p>

        <p style="font-size:32px;font-weight:bold;color:#1a73e8;text-align:center;">
            {code}
        </p>

        <p>Код действует 10 минут.</p>
        <hr>
        <p style="font-size:12px;color:#888;">Если это были не вы — срочно смените пароль.</p>
      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
