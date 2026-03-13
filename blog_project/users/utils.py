import threading
import logging
from django.core.mail import send_mail,send_mass_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return Response(payload, status=status_code)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh.access_token['role']  = user.role
    refresh.access_token['email'] = user.email
    return {
        'access_token':  str(refresh.access_token),
        'refresh_token': str(refresh),
    }

def send_reset_email_async(to_email, username, reset_link):
    def _send():
        try:
            send_mail(
                subject="Reset your Blog Platform password",
                message=(
                    f"Hi {username},\n\n"
                    f"You requested a password reset.\n"
                    f"Click the link below — it expires in 15 minutes:\n\n"
                    f"{reset_link}\n\n"
                    f"If you didn't request this, ignore this email.\n\n"
                    f"— Blog Platform Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            logger.info(f"Reset email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send reset email to {to_email}: {e}")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def send_subscriber_emails_async(blog):
    from .models import Subscription   # local import avoids any circular risk

    def _send():
        emails      = Subscription.objects.get_subscriber_emails(blog.author)
        if not emails:
            return

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        blog_link    = f"{frontend_url}/blogs/{blog.slug}"

        subject = f"{blog.author.username} published a new post!"
        body    = (
            f"Hi,\n\n"
            f"{blog.author.username} just published:\n\n"
            f"  {blog.title}\n\n"
            f"Read it here: {blog_link}\n\n"
            f"— Blog Platform Team"
        )
        datatuple = tuple(
            (subject, body, settings.DEFAULT_FROM_EMAIL, [email])
            for email in emails
        )
        send_mass_mail(datatuple, fail_silently=True)

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()