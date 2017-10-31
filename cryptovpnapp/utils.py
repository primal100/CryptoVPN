from allauth.account.models import EmailAddress
from .collect_metadata import check_registration

def user_verify_email(user):
    if check_registration():
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)

def user_verify_email_with_check_existing(user):
    if check_registration():
        emailaddress, created = EmailAddress.objects.get_or_create(user=user, email=user.email, primary=True)
        if not emailaddress.verified:
            emailaddress.verified = True
            emailaddress.save()