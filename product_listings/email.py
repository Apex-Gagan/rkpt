from django.conf import settings
from django.core.mail import EmailMessage, get_connection


def send_email(name, email, mobile, message):
    connection = get_connection()

    # Create the email
    i = 0
    if i <= 0:
        try:
            # Create a connection to the SMTP server

            email = EmailMessage(
                subject="No Reply - Website Form Submission | Rakesh Packers",
                body=f"Hi Vaibhav from Rakesh Packers, \n\n "
                f"Someone has contacted us. Below are the details.\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n"
                f"Mobile: {mobile if mobile else 'Not provided'}\n"
                f"Message: {message}",
                from_email=f"Rakesh Packers Website <{settings.EMAIL_HOST_USER}>",
                to=[
                    "rakeshpackers5@gmail.com",
                ],
                connection=connection,
            )

            email.send()
            i += 1
            connection.close()
        except Exception:
            return None
