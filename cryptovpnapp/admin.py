from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from .models import User, Service, SubscriptionType, Subscription, Address, Invoice, Transaction, RefundRequest, Comment

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


class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    readonly_fields =  [f.name for f in LogEntry._meta.get_fields()]

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link

    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'

    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request) \
            .prefetch_related('content_type')

class CustomUserAdmin(UserAdmin):
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
    list_display = ('hash', 'coin', 'invoice', 'time', 'total_received')

class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'invoice', 'address', 'transaction_hash', 'amount_requested',
                    'requested_on', 'last_modified', 'resolved', 'is_active')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'refund_request', 'created_on', 'last_modified', 'is_active')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(RefundRequest, RefundRequestAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
admin.site.unregister(Group)