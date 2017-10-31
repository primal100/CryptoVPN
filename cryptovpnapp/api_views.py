from drfxtra.mixins import XtraViewSetMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.mixins import CreateModelMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_auth.registration import views
from .models import (
    Service, SubscriptionType, Subscription, Address, Invoice, RefundRequest, Comment
)
from .serializers import (
    ServiceSerializer, SubscriptionTypeSerializer, SubscriptionSerializer, AddressSerializer,
InvoiceSerializer, RefundRequestSerializer, CommentSerializer
)

UserModel = get_user_model()

views.LoginView.authentication_classes = (JSONWebTokenAuthentication,)

class XtraViewSetMixinWithDeactivate(XtraViewSetMixin):
    def perform_destroy(self, instance):
        instance.deactivate()
        if self.log_write_entres:
            self.log_deletion(instance, 'deleted')


class ServiceViewset(XtraViewSetMixinWithDeactivate, ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = ()
    ordering = ('priority', 'name')
    filter_fields = ('name',)
    ordering_fields = ('id', 'name')
    search_fields = ('name',)
    autocomplete_fields = ("name",)


class SubscriptionTypeViewset(XtraViewSetMixinWithDeactivate, ReadOnlyModelViewSet):
    queryset = SubscriptionType.objects.filter(is_active=True)
    serializer_class = SubscriptionTypeSerializer
    permission_classes = ()
    ordering = ('priority', 'name')
    filter_fields = ('name', 'currency', 'price', 'period', 'service')
    ordering_fields = ('id', 'name', 'price', 'currency', 'period')
    search_fields = ('name', 'currency')
    autocomplete_fields = ('name')
    autocomplete_foreign_keys = {'service':{'queryset': Service.objects.filter(is_active=True), 'related_field': 'name'}}


class SubscriptionViewset(XtraViewSetMixinWithDeactivate, ReadOnlyModelViewSet, CreateModelMixin):
    queryset = Subscription.objects.filter(is_active=True)
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('-last_subscribed',)
    filter_fields = ('id', 'subscription_type', 'last_subscribed', 'expires')
    ordering_fields = ('id', 'last_subscribed', 'expires')
    set_field_value_to_current_user_on_create = 'user'
    autocomplete_foreign_keys = {'subscription_type': {'queryset': SubscriptionType.objects.filter(is_active=True)}}
    log = True

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class AddressViewset(XtraViewSetMixin, ReadOnlyModelViewSet, CreateModelMixin):
    queryset = Address.objects.filter(is_active=True, test_address=settings.TEST_ADDRESSES)
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('public',)
    filter_fields = ('public', 'coin', 'subscription')
    ordering_fields = ('public', 'coin')
    search_fields = ('public', 'coin')
    autocomplete_foreign_keys = {'subscription_type': {'queryset': SubscriptionType.objects.filter(is_active=True)}}

    def get_queryset(self):
        return self.queryset.filter(subscription__user=self.request.user)

class InvoiceViewset(XtraViewSetMixin, ReadOnlyModelViewSet, CreateModelMixin):
    queryset = Invoice.objects.filter()
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('start_time',)
    filter_fields = ('address', 'start_time', 'expiry_time', 'currency', 'fiat_due', 'crypto_due', 'paid', 'paid_time', 'actual_paid')
    ordering_fields = ('start_time', 'expiry_time', 'currency', 'fiat_due', 'crypto_due', 'paid', 'paid_time', 'actual_paid')
    search_fields = ('currency',)
    autocomplete_foreign_keys = {'address': {'queryset': Address.objects.filter(is_active=True, test_address=settings.TEST_ADDRESSES)}}
    log = True

    def get_queryset(self):
        return self.queryset.filter(address__subscription__user=self.request.user)

class RefundRequestViewset(XtraViewSetMixinWithDeactivate, ModelViewSet):
    queryset = RefundRequest.objects.filter(is_active=True)
    serializer_class = RefundRequestSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('requested_on',)
    filter_fields = ('amount_requested', 'transaction_hash', 'requested_on', 'last_modified', 'resolved')
    ordering_fields = ('requested_on', 'solved', 'amount_requsted')
    search_fields = ('transaction_id')
    autocomplete_foreign_keys = {'address': {'queryset': Address.objects.filter(is_active=True, test_address=settings.TEST_ADDRESSES)},
                                 'service': {'queryset': Service.objects.filter(is_active=True)},
                                 'invoice': {'queryset': Invoice.objects.filter()},
                                 }
    log = True

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class CommentViewset(XtraViewSetMixinWithDeactivate, ModelViewSet):
    queryset = Comment.objects.filter(is_active=True)
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('created_on',)
    filter_fields = ('user', 'refund_request', 'created_on', 'last_modified')
    ordering_fields = ('created_on', 'last_modified')
    search_fields = ('text',)
    log = True

    def get_queryset(self):
        return self.queryset.filter(refund_request__user=self.request.user)