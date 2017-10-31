from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from .fields import CryptoField, FiatField
import pytz

class User(AbstractUser):
    first_name = None
    last_name = None

    def deactivate(self):
        for subscription in self.subscriptions.filter(is_active=True):
            subscription.deactivate()
        self.is_active = False
        self.save()

class Service(models.Model):
    name = models.CharField(max_length=32)
    priority = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        super(Service, self).save(*args, **kwargs)
        if not self.priority:
            latest_priority = Service.objects.values_list('priority', flat=True).order_by('-priority').first()
            self.priority = latest_priority + 1
            super(Service, self).save(*args, **kwargs)

    def add_subscription_type(self, price, period=None):
        subscription_type = SubscriptionType(service=self, price=price, period=period)
        subscription_type.save()
        return subscription_type

    def has_valid_subscription(self, user):
        response = {'has': False, 'is_valid': False}
        if not user.is_authenticated:
            return False
        subscription_types = self.subscription_types.filter(is_active=True)
        for st in subscription_types:
            res = st.has_valid_subscription(user)
            if res['is_valid']:
                return {'has':True, 'is_valid': True}
            if res['has']:
                response['has'] = True
        return response

    def __str__(self):
        return self.name

    def deactivate(self):
        for subscription_type in self.subscription_types.filter(is_active=True):
            subscription_type.deactivate()
        self.is_active = False
        self.save()

class SubscriptionType(models.Model):
    name = models.CharField(max_length=48)
    priority = models.IntegerField(null=True, blank=True)
    price = FiatField(default=settings.DEFAULT_SUBSCRIPTION_PRICE)
    currency = models.CharField(default="USD", max_length=12)
    period = models.DurationField(default=timedelta(days=30))
    service = models.ForeignKey(Service, related_name="subscription_types")
    is_active = models.BooleanField(default=True)

    def has_valid_subscription(self, user):
        if user.is_authenticated:
            sub = self.subscriptions.filter(user=user, is_active=True).first()
            if sub and sub.check_subscription_paid:
                return {'has': bool(sub), 'is_valid': True}
            return {'has': bool(sub), 'is_valid': False}
        return {'has': False, 'is_valid': False}

    def save(self, *args, **kwargs):
        super(SubscriptionType, self).save(*args, **kwargs)
        if not self.priority:
            latest_priority = SubscriptionType.objects.values_list('priority', flat=True).order_by('-priority').first()
            if not latest_priority and not latest_priority == 0:
                latest_priority = 0
            self.priority = latest_priority + 1
            super(SubscriptionType, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def deactivate(self):
        for subscription in self.subscriptions.filter(is_active=True):
            subscription.deactivate()
        self.is_active = False
        self.save()

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name="subscriptions", editable=False)
    subscription_type = models.ForeignKey(SubscriptionType, verbose_name=_("subscription type"), related_name="subscriptions")
    last_subscribed = models.DateTimeField(_('last subscribed'), null=True)
    expires = models.DateTimeField(_('subscription expires'), null=True)
    auto_renewal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "%s %s" % (self.user, self.subscription_type)

    def post_save(self, coin):
        address = self.new_address(coin)
        invoice = Invoice(address=address)
        invoice.save()
        return invoice

    def new_address(self, coin):
        address = Address.objects.filter(subscription__isnull=True, coin=coin, is_active=True, test_address=settings.TEST_ADDRESSES).first()
        address.subscription = self
        address.save()
        return address

    def check_subscription_paid(self):
        if self.already_subscribed:
            return True
        addresses = self.addresses.filter(is_active=True)
        for address in addresses:
            paid_time = address.check_subscription_paid()
            if paid_time:
                self.last_subscribed = paid_time
                self.expires = paid_time + self.subscription_type.period
                self.save()
                return True
        return False

    @property
    def already_subscribed(self):
        if self.expires:
            return datetime.utcnow().replace(tzinfo=pytz.utc) <= self.expires
        return False

    def deactivate(self):
        for address in self.addresses.filter(is_active=True):
            address.deactivate()
        self.is_active = False
        self.save()

class OpenInvoiceAlreadyExists(Exception):
    pass

class Address(models.Model):
    public = models.CharField(max_length=64, primary_key=True, editable=False)
    subscription = models.ForeignKey(Subscription, related_name="addresses", null=True, editable=False)
    coin = models.CharField(max_length=12, choices=settings.COINS, editable=False)
    is_active = models.BooleanField(default=True)
    test_address = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        return self.public

    def save(self, *args, **kwargs):
        if not self.pk:
            address = Address.objects.filter(subscription__isnull=True, coin=self.coin, is_active=True, test_address=settings.TEST_ADDRESSES).first()
            address.subscription = self.subscription
            super(Address, address).save(*args, **kwargs)
            self.id = address.id
        else:
            super(Address, self).save(*args, **kwargs)

    def coin_api(self):
        coin_class_str = settings.COIN_CLASSES[self.coin]
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def check_invoice_payments(self, subscription_period):
        invoices = self.invoices.filter(paid=False, start_time__gt=datetime.now() - subscription_period)
        if invoices:
            if self.test_address:
                transactions = self.coin_api().generate_test_transaction(invoices)
            else:
                transactions = self.coin_api().get_transactions(invoices)
            transactions.sort(key=lambda t: t.datetime)
            for invoice in invoices:
                crypto_paid = 0
                for t in transactions:
                    if t.datetime >= invoice.start_time and t.datetime <= invoice.expiry_time:
                        transaction = Transaction.objects.filter(hash=t.hash).first()
                        if not transaction:
                            transaction = Transaction(hash=t.hash, invoice=invoice, time=t.datetime, total_received=t.total_received, total_paid=t.total_paid, coin=self.coin, fee=t.fee)
                            transaction.save()
                        crypto_paid += transaction.total_paid
                        if crypto_paid >= invoice.crypto_due and not invoice.paid:
                            invoice.paid = True
                            invoice.paid_time = transaction.time
                invoice.actual_paid = crypto_paid
                invoice.save()

    def check_subscription_paid(self, subscription=None):
        if not subscription:
            subscription = self.subscription
        self.check_invoice_payments(subscription.subscription_type.period)
        return self.invoices.filter(paid_time__gt=datetime.now() - subscription.subscription_type.period).values_list('paid_time', flat=True).first()

    def deactivate(self):
        self.is_active = False
        self.save()

class Invoice(models.Model):
    address = models.ForeignKey(Address, related_name="invoices", editable=False)
    crypto_due = CryptoField()
    fiat_due = FiatField()
    currency = models.CharField(max_length=12)
    start_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    paid = models.BooleanField(default=False)
    paid_time = models.DateTimeField(null=True)
    actual_paid = CryptoField(null=True)

    def save(self, subscription=None, *args, **kwargs):
        if self.pk:
            super(Invoice, self).save(*args, **kwargs)
        else:
            if not subscription:
                subscription = self.address.subscription
            now = datetime.now()
            exists = Invoice.objects.filter(address=self.address, expiry_time__gt=now).exists()
            if exists:
                raise OpenInvoiceAlreadyExists
            else:
                self.fiat_due = subscription.subscription_type.price
                period = subscription.subscription_type.period
                self.currency = subscription.subscription_type.currency
                self.crypto_due = self.address.coin_api().convert_price_to_crypto(self.currency, self.fiat_due)
                self.expiry_time = now + period
                super(Invoice, self).save(*args, **kwargs)

    def within_time_period(self, timestamp):
        return timestamp >= self.start_time and timestamp <= self.expiry_time

    def __str__(self):
        return str(self.pk)

class Transaction(models.Model):
    hash = models.CharField(max_length=128, primary_key=True, editable=False)
    invoice = models.ForeignKey(Invoice)
    time = models.DateTimeField()
    coin = models.CharField(max_length=12, choices=settings.COINS)
    total_received = CryptoField()
    total_paid = CryptoField()
    fee = CryptoField()

    def __str__(self):
        return self.hash

class RefundRequest(models.Model):
    user = models.ForeignKey(User, related_name="refund_requests", editable=False)
    service = models.ForeignKey(Service, null=True, related_name="refund_requests")
    invoice = models.ForeignKey(Invoice, null=True, related_name="refund_requests")
    address = models.ForeignKey(Address, null=True, related_name="refund_requests")
    transaction_hash = models.CharField(max_length=64, null=True)
    amount_requested = CryptoField(null=True)
    requested_on = models.DateTimeField(auto_now_add=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True)
    text = models.TextField(null=True)
    resolved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.pk

    def deactivate(self):
        for comment in self.comments.filter(is_active=True):
            comment.deactivate()
        self.is_active = False
        self.save()

class Comment(models.Model):
    user = models.ForeignKey(User, editable=False)
    refund_request = models.ForeignKey(RefundRequest, related_name="comments")
    text = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.pk

    def deactivate(self):
        self.is_active = False
        self.save()