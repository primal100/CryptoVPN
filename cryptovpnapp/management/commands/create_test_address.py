from django.core.management.base import BaseCommand
from cryptovpnapp.models import Address
import uuid

class Command(BaseCommand):
    help = 'Generates test addresses'

    def handle(self, *args, **options):
        addresses = [uuid.uuid4().hex.upper() for i in range(0, 50)]
        address_instances = [Address(public=a, test_address=True, coin="BTC") for a in addresses]
        Address.objects.bulk_create(address_instances)