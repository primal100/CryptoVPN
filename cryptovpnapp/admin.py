from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, Service, SubscriptionType, Subscription, Address, Invoice, Transaction

class ReadOnlyAdmin(admin.ModelAdmin):
    change_form_template = "admin/read-only-view.html"

    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdmin, self).__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request):
        actions = super(ReadOnlyAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_staff', 'is_superuser', 'is_active', )

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'is_active')

class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'currency', 'price', 'period', 'service', 'is_active')

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'last_subscribed', 'expires', 'is_active')

class AddressAdmin(admin.ModelAdmin):
    list_display = ('public', 'coin', 'subscription', 'test_address', 'is_active')

class InvoiceAdmin(ReadOnlyAdmin):
    list_display = ('address', 'currency', 'fiat_due', 'crypto_due', 'start_time', 'expiry_time', 'paid', 'paid_time', 'actual_paid')

class TransactionAdmin(ReadOnlyAdmin):
    list_display = ('hash', 'coin', 'invoice', 'time', 'total_paid', 'fee', 'total_received')

class RefundRequestAdmin(ReadOnlyAdmin):
    list_display = ('user', 'service', 'invoice', 'address', 'transaction_hash', 'amount_requested',
                    'requested_on', 'last_modified', 'resolved', 'is_active')

class CommentAdmin(ReadOnlyAdmin):
    list_display = ('user', 'refund_request', 'created_on', 'last_modified', 'is_active')

admin.site.register(User, UserAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.unregister(Group)