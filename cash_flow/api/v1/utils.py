from django.core.mail import send_mail, EmailMessage
from django.conf import settings


class Util:
    @staticmethod
    def send_email(data, file):
        try:
            subject = data['subject']
            body = data['body']
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = data['to_email']

            email = EmailMessage(subject, body, from_email, to_email)
            email.attach_file(file)
            email.send()
            return True
        except Exception as e:
            return False
