from rest_framework import routers
from .api_views import (
    ServiceViewset, SubscriptionViewset, SubscriptionTypeViewset, AddressViewset,
    InvoiceViewset, RefundRequestViewset, CommentViewset
)

cryptovpn_api_urls = routers.DefaultRouter()
cryptovpn_api_urls.register("services", ServiceViewset),
cryptovpn_api_urls.register("subscription_types", SubscriptionTypeViewset)
cryptovpn_api_urls.register("subscriptions", SubscriptionViewset)
cryptovpn_api_urls.register("addresses", AddressViewset)
cryptovpn_api_urls.register("invoices", InvoiceViewset)
cryptovpn_api_urls.register("refund_requests", RefundRequestViewset)
cryptovpn_api_urls.register("comments", CommentViewset)