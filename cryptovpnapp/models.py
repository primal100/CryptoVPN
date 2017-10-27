from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from .fields import CryptoField, FiatField

class User(AbstractUser):
    first_name = None
    last_name = None

class Service(models.Model):
    name = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)

    def add_subscription_type(self, price, period=None):
        subscription_type = SubscriptionType(service=self, price=price, period=period)
        subscription_type.save()
        return subscription_type

    def has_valid_subscription(self, user):
        subscription_types = self.subscription_types.filter(active=True)
        for st in subscription_types:
            sub = st.subscriptions.get(user=user, active=True)
            if sub.check_subscription_paid:
                return True
        return False

    def __str__(self):
        return self.name

class SubscriptionType(models.Model):
    name = models.CharField(max_length=48)
    price = FiatField(default=settings.DEFAULT_SUBSCRIPTION_PRICE)
    currency = models.CharField(default="USD", max_length=12)
    period = models.DurationField(default=timedelta(days=30))
    service = models.ForeignKey(Service, related_name="subscription_types")
    is_active = models.BooleanField(default=True)

    def create_subscription(self, user, coin):
        subscription = Subscription(user=user, subscription_type=self)
        subscription.save()
        address = subscription.new_address(coin)
        invoice = address.generate_invoice(subscription)
        return invoice

    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name="subscriptions")
    subscription_type = models.ForeignKey(SubscriptionType, verbose_name=_("subscription type"), related_name="subscriptions")
    last_subscribed = models.DateTimeField(_('last subscribed'), null=True)
    subscription_expires = models.DateTimeField(_('subscription expires'), null=True)
    auto_renewal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "%s %s" % (self.user, self.subscription_type)

    #class Meta:
    #    unique_together = (("user", "subscription_type"),)

    def new_address(self, coin):
        address = Address.objects.filter(subscription__isnull=True, coin=coin, is_active=True).first()
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
                self.subscription_expires = paid_time + timedelta(days=self.subscription_type.period)
                return True
        return False

    @property
    def already_subscribed(self):
        if self.subscription_expires:
            return datetime.now() <= self.subscription_expires
        return False

class OpenInvoiceAlreadyExists(Exception):
    pass


class Address(models.Model):
    public = models.CharField(max_length=64, primary_key=True)
    subscription = models.ForeignKey(Subscription, related_name="subscriptions", null=True)
    coin = models.CharField(max_length=12, choices=settings.COINS)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        return self.public

    def coin_api(self):
        coin_class_str = "cryptovpnapp.%s.Blockchain" % self.coin.lower()
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def check_invoice_payments(self, subscription_period):
        invoices = self.invoices.filter(paid=False, start_time__gt=datetime.now() - timedelta(days=subscription_period))
        if invoices:
            transactions = self.coin_api().get_transactions(subscription_period)
            transactions.sort(key=lambda t: t.datetime)
            for invoice in invoices:
                crypto_paid = 0
                for t in transactions:
                    if t.datetime >= invoice.start_time and t.datetime <= invoice.expiry_time:
                        Transaction(tx_hash=t.hash, invoice=invoice, time=t.datetime, total_value=t.total_value, coin=self.coin).save()
                        crypto_paid += t.total_value
                        if crypto_paid >= invoice.crypto_price and not invoice.paid:
                            invoice.paid = True
                            invoice.paid_time = t.datetime
                invoice.actual_paid = crypto_paid
                invoice.save()

    def check_subscription_paid(self, subscription=None):
        if not subscription:
            subscription = self.subscription
        self.check_invoice_payments(subscription.period)
        return self.invoices.filter(paid_time__gt=datetime.now()-timedelta(days=subscription.period)).values_list('paid_time', flat=True).first()

    def generate_invoice(self, subscription=None):
        if not subscription:
            subscription = self.subscription
        now = datetime.now()
        exists = Invoice.objects.filter(address=self, expiry_time__gt=now).exists()
        if exists:
            raise OpenInvoiceAlreadyExists
        else:
            fiat_price = subscription.subscription_type.price
            period = subscription.subscription_type.period
            currency = subscription.subscription_type.currency
            crypto_price = self.coin_api().convert_price_to_crypto(currency, fiat_price)
            invoice = Invoice(address=self, fiat_price=fiat_price, currency=currency, crypto_price=crypto_price)
            invoice.expiry_time = invoice.start_time + timedelta(minutes=period)
            invoice.save()
            return invoice

class Invoice(models.Model):
    address = models.ForeignKey(Address, related_name="invoices")
    crypto_due = CryptoField()
    fiat_due = FiatField()
    currency = models.CharField(max_length=12)
    start_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    paid = models.BooleanField(default=False)
    paid_time = models.DateTimeField(null=True)
    actual_paid = CryptoField()

    def __str__(self):
        return self.pk

class Transaction(models.Model):
    hash = models.CharField(max_length=128, primary_key=True)
    invoice = models.ForeignKey(Invoice)
    time = models.DateTimeField()
    coin = models.CharField(max_length=12, choices=settings.COINS)
    total_value = CryptoField()
    fee = CryptoField()

    def __str__(self):
        return self.tx_hash

class RefundRequest(models.Model):
    user = models.ForeignKey(User, related_name="refund_requests")
    service = models.ForeignKey(Service, null=True, related_name="refund_requests")
    invoice = models.ForeignKey(Invoice, null=True, related_name="refund_requests")
    address = models.ForeignKey(Address, null=True, related_name="refund_requests")
    transaction_id = models.CharField(max_length=64, null=True)
    amount_requested = CryptoField(null=True)
    reqested_on = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=True)

    def __str__(self):
        return self.pk

class Comments(models.Model):
    user = models.ForeignKey(User)
    refund_request = models.ForeignKey(RefundRequest, related_name="comments")
    text = models.TextField()

    def __str__(self):
        return self.pk