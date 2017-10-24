from datetime import datetime, timedelta
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.utils import six, timezone
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _


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

    def refresh_last_subscribed(self):
        self.last_subscribed = datetime.now()
        self.save()

    @property
    def subscription_expires(self):
        return self.last_subscribed + timedelta(days=self.subscription_period)

    @property
    def already_subscribed(self):
        return datetime.now() <= self.subscription_expires

    subscription_price = models.IntegerField(_('subscription period'), default=settings.DEFAULT_SUBSCRIPTION_PRICE)

    invoices = models.BooleanField(default=True)

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

    def check_subscription(self):
        if self.already_subscribed:
            return True
        value = self.get_full_fiat_value()
        if value >= self.subscription_price:
            self.refresh_subscription_period()
            return True
        return False

    def get_fiat_values(self):
        addresses = {}
        for address in self.addresses.all():
            addresses[address.public] = address.get_fiat_values(period=self.subscription_period)['full_value']
        full_value = sum([v['full_value'] for v in addresses.values()])
        return {
            'full_value': full_value,
            'addresses': addresses
        }

    def get_full_fiat_value(self):
        data = self.get_fiat_values()
        return data['full_value']

class AddressManager(models.Manager):

    def create_address(self, user, coin):
        address = self.model(user=user, coin=coin)
        coin_api = address.coin_api()
        address.public = coin_api.new_address()
        address.save()
        return self.public

class Address(models.Model):

    def coin_api(self):
        coin_class_str = "cryptovpnapp.%s.CoinWallet" % self.coin.lower()
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def get_fiat_values(self, period=None):
        coin_api = self.coin_api()
        transactions = coin_api.get_transactions(period=period)
        for t in transactions:
            t.price = Price.objects.get_archived_price(self.coin, t.timestamp)
        full_value = sum([t.price for t in transactions])
        return {
            'address_full_value': full_value,
            'transactions': transactions
        }


    user = models.ForeignKey(User, related_name="addresses")
    coin = models.CharField(max_length=12, choices=settings.COINS)
    public = models.CharField(max_length=64)

    objects = AddressManager()


class PriceManager(models.Manager):
    @property
    def coin_api(self):
        coin_class_str = "cryptovpnapp.%s.Exchange" % self.coin.lower()
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def add_price(self, coin):
        from_time = datetime.now()
        interval = settings.BTC_PRICE_UPDATE_INTERVAL
        price = self.coin_api.get_current_price()
        model = self.model(coin=coin, price=price, from_time=from_time)
        model.to_time = from_time + timedelta(minutes=interval)
        model.save()
        return model.price

    def get_archived_price(self, coin, timestamp):
        price = self.filter(coin=coin, from_time__lt=timestamp, to_time__gt=timestamp).values_list('price', flat=True).first()
        return price

    def get_current_price_or_add(self, coin):
        price = self.get_archived_price(coin, datetime.now())
        if not price:
            price = self.add_price(coin)
        return price

class Price(models.Model):
    coin = models.CharField(max_length=12, choices=settings.COINS)
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()
    price = models.DecimalField()

    objects = PriceManager()

class RefundRequest(models.Model):
    user = models.ForeignKey(User)
    transaction_id = models.CharField(max_length=64, null=True)
    amount_requested = models.DecimalField(decimal_places=10, null=True)
    reqested_on = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=True)

class Comments(models.Model):
    user = models.ForeignKey(User)
    refund_request = models.ForeignKey(RefundRequest, related_name="comments")
    text = models.TextField()