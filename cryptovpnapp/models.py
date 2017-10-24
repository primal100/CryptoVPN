from datetime import datetime
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.utils import six, timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from encrypted_model_fields.fields import EncryptedCharField


class User(AbstractBaseUser):
    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    last_subscribed = models.DateTimeField(_('last subscribed'), null=True)

    subscription_period = models.DurationField(_('subscription period'), default=settings.DEFAULT_SUBSCRIPTION_PERIOD)

    def refresh_subscription_period(self):
        self.subscription_period = datetime.now()
        self.save()

    @property
    def already_subscribed(self):
        return (datetime.now() - self.last_subscribed) <= self.subscription_period

    subscription_price = models.IntegerField(_('subscription period'), default=settings.DEFAULT_SUBSCRIPTION_PRICE)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def clean(self):
        super(User, self).clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_addresses_value(self):
        value = 0
        for address in self.addresses:
            value += address.get_value(self.subscription_period)
        return value

    def check_subscription(self):
        if self.already_subscribed:
            return True
        value = self.get_addresses_value()
        if value >= self.subscription_price:
            self.refresh_subscription_period()
            return True
        return False

class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses")
    coin = models.CharField(max_length=32, choices=settings.COINS)
    public = models.CharField(max_length=64)

    @property
    def coin_api(self):
        coin_class_str = "cryptovpnapp.%s.CoinWallet" % self.coin.lower()
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def create_address(self, user, coin):
        self.user = user
        self.coin = coin
        self.public = self.coin_api.new_address()
        self.save()
        return self.public

