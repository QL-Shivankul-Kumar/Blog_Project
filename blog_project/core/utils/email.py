import threading
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings


def send_reset_email_async(to_email: str, username: str, reset_link: str) -> None:
    def _send():
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
    threading.Thread(target=_send, daemon=True).start()


def send_subscriber_emails_async(blog) -> None:
    from apps.users.models import Subscription  # local import to avoid circular

    def _send():
        emails = Subscription.objects.get_subscriber_emails(blog.author)
        if not emails:
            return
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        blog_link    = f"{frontend_url}/blogs/{blog.slug}"
        subject      = f"{blog.author.username} published a new post!"
        body         = (
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

    threading.Thread(target=_send, daemon=True).start()