from drfxtra.serializers import XtraModelSerializer, PKStringRelatedField
from rest_framework import fields, relations
from django.contrib.auth import get_user_model
from .models import (
    Service, SubscriptionType, Subscription, Address, Invoice, Transaction, RefundRequest, Comment
)

UserModel = get_user_model()


class UserDetailsSerializer(XtraModelSerializer):

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'is_staff', 'is_superuser', 'last_login')

class CommentSerializer(XtraModelSerializer):
    serializer_related_field = PKStringRelatedField

    class Meta:
        model = Comment
        fields = ('id', 'user', 'refund_request', 'text', 'created_on', 'last_modified')
        read_only_fields = ('id', 'user', 'created_on', 'last_modified')

class CommentEmbeddedSerializer(XtraModelSerializer):
    serializer_related_field = PKStringRelatedField

    class Meta:
        model = Comment
        fields = ('id', 'user', 'text', 'created_on', 'last_modified')
        read_only_fields = ('id', 'user', 'created_on', 'last_modified')

class RefundRequestSerializer(XtraModelSerializer):
    service = PKStringRelatedField(required=False, many=False, queryset=Service.objects.all())
    address = relations.PrimaryKeyRelatedField(required=False, many=False, queryset=Service.objects.all())
    comments = CommentEmbeddedSerializer(many=True, read_only=True)

    class Meta:
        model = RefundRequest
        fields = (
        'id', 'service', 'invoice', 'address', 'transaction_hash', 'amount_requested',
        'requested_on', 'last_modified', 'text', 'resolved', 'comments')
        read_only_fields = ('id', 'requested_on', 'last_modified', 'comments')

class TransactionEmbeddedSerializer(XtraModelSerializer):

    class Meta:
        model = Transaction
        fields = ('hash', 'time', 'coin', 'total_paid', 'total_received', 'fee')

class InvoiceSerializer(XtraModelSerializer):
    transactions = TransactionEmbeddedSerializer(many=True)

    class Meta:
        model = Invoice
        fields = (
        'id', 'address', 'crypto_due', 'fiat_due', 'currency', 'start_time', 'expiry_time', 'paid', 'paid_time',
        'actual_paid', 'transactions')
        read_only_fields = ('id', 'crypto_due', 'fiat_due', 'currency', 'start_time', 'expiry_time', 'paid', 'paid_time',
        'actual_paid', 'transactions')

class InvoiceEmbeddedSerializer(XtraModelSerializer):

    class Meta:
        model = Invoice
        fields = (
        'id', 'crypto_due', 'fiat_due', 'currency', 'start_time', 'expiry_time', 'paid', 'paid_time',
        'actual_paid')


class AddressSerializer(XtraModelSerializer):

    class Meta:
        model = Address
        fields = ('public', 'coin', 'invoices')
        read_only_fields = ('public', 'invoices')

class AddressEmbeddedSerializer(XtraModelSerializer):
    invoices = InvoiceEmbeddedSerializer(many=True)
    class Meta:
        model = Address
        fields = ('public', 'coin', 'invoices')
        read_only_fields = ('public', 'coin', 'invoices')

class SubscriptionSerializer(XtraModelSerializer):
    addresses = AddressEmbeddedSerializer(many=True, read_only=True)
    valid = fields.SerializerMethodField()
    coin = fields.CharField(max_length=12, write_only=True)

    def get_valid(self, instance):
        return instance.check_subscription_paid()

    def save(self, **kwargs):
        coin = self.validated_data.pop('coin')
        instance = super(SubscriptionSerializer, self).save(**kwargs)
        instance.post_save(coin)
        return instance

    class Meta:
        model = Subscription
        fields = ('id', 'subscription_type', 'coin', 'last_subscribed', 'expires', 'addresses', 'valid')
        read_only_fields = ('id', 'last_subscribed', 'expires', 'addresses', 'valid')
        write_only_fields = ("coin",)

class DaysDurationField(fields.DurationField):
    def to_representation(self, value):
        return value.days

class SubscriptionTypeSerializer(XtraModelSerializer):
    current_subscription = fields.SerializerMethodField()
    period = DaysDurationField()

    def get_current_subscription(self, instance):
        return instance.has_valid_subscription(self.context['request'].user)

    class Meta:
        model = SubscriptionType
        fields = ('id', 'name', 'currency', 'price', 'period', 'service', 'current_subscription')

class SubscriptionTypeEmbeddedSerializer(SubscriptionTypeSerializer):

    class Meta:
        model = SubscriptionType
        fields = ('id', 'name', 'currency', 'price', 'period', 'current_subscription')

class ServiceSerializer(XtraModelSerializer):
    current_subscription = fields.SerializerMethodField()
    subscription_types = SubscriptionTypeEmbeddedSerializer(many=True, read_only=True)

    def get_current_subscription(self, instance):
        return instance.has_valid_subscription(self.context['request'].user)

    class Meta:
        model = Service
        fields = ('name', 'subscription_types', 'current_subscription')


