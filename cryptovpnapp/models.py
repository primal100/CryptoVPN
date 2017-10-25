from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

class User(AbstractUser):
    first_name = None
    last_name = None

class Service(models.Model):
    name = models.CharField(max_length=32)
    active = models.BooleanField(default=True)

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
    price = models.DecimalField(decimal_places=2, default=settings.DEFAULT_SUBSCRIPTION_PRICE)
    currency = models.CharField(default="USD", max_length=12)
    period = models.DurationField(default=timedelta(days=30))
    service = models.ForeignKey(Service, related_name="subscription_types")
    active = models.BooleanField(default=True)

    def create_subscription(self, user, coin):
        subscription = Subscription(user=user, subscription_type=self)
        subscription.save()
        address = Address(subscription=subscription, coin=coin)
        address.save()
        invoice = address.generate_invoice(subscription)
        return invoice

    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(User, related_name="subscriptions")
    subscription_type = models.ForeignKey(SubscriptionType, verbose_name=_("subscription type", related_name="subscriptions"))
    last_subscribed = models.DateTimeField(_('last subscribed'), null=True)
    subscription_expires = models.DateTimeField(_('subscription expires'), null=True)
    auto_renewal = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "%s %s" % (self.user, self.subscription_type)

    class Meta:
        unique_together = (("user", "subscription_type"),)

    def check_subscription_paid(self):
        if self.already_subscribed:
            return True
        addresses = self.addresses.filter(active=True)
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
    subscription = models.ForeignKey(Subscription, related_name="addresses")
    coin = models.CharField(max_length=12, choices=settings.COINS)
    public = models.CharField(max_length=64)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.public

    def coin_api(self):
        coin_class_str = "cryptovpnapp.%s.CoinWallet" % self.coin.lower()
        coin_class = import_string(coin_class_str)
        return coin_class(self)

    def save(self, **kwargs):
        if not self.public:
            coin_api = self.coin_api()
            self.public = coin_api.new_address()
        super(Address, self).save(**kwargs)

    def check_invoice_payments(self, subscription_period):
        invoices = self.invoices.filter(paid=False, start_time__gt=datetime.now() - timedelta(days=subscription_period))
        if invoices:
            transactions = self.coin_api().get_transactions(subscription_period)
            transactions.sort(key=lambda t: t.datetime)
            for invoice in invoices:
                crypto_paid = 0
                for t in transactions:
                    if t.datetime >= invoice.start_time and t.datetime <= invoice.expiry_time:
                        Transaction(tx_index=t.tx_index, invoice=invoice, time=t.datetime, amount=t.total_value).save()
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
    crypto_due = models.DecimalField(decimal_places=12)
    fiat_due = models.DecimalField(decimal_places=2)
    currency = models.CharField(max_length=12)
    start_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    paid = models.BooleanField(default=False)
    paid_time = models.DateTimeField(null=True)
    actual_paid = models.DecimalField(decimal_places=12)

    def __str__(self):
        return self.pk

class Transaction(models.Model):
    tx_index = models.CharField(max_length=128)
    invoice = models.ForeignKey(Invoice)
    time = models.DateTimeField()
    amount = models.DecimalField(decimal_places=12)

    def __str__(self):
        return self.tx_index

class RefundRequest(models.Model):
    user = models.ForeignKey(User, related_name="refund_requests")
    service = models.ForeignKey(Service, null=True, related_name="refund_requests")
    invoice = models.ForeignKey(Invoice, null=True, related_name="refund_requests")
    address = models.ForeignKey(Address, null=True, related_name="refund_requests")
    transaction_id = models.CharField(max_length=64, null=True)
    amount_requested = models.DecimalField(decimal_places=10, null=True)
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