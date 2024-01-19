from django.core.mail import send_mail, EmailMessage
from django.conf import settings


def send_email(subject, message, recipient_list, attachments=None, from_email=None):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False
    )


def send_email_with_attachment(subject, message, recipient_list, attachments=None, from_email=None):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=recipient_list,
        attachments=attachments if attachments else [],
    )
    email.send()
