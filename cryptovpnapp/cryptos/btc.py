from datetime import datetime
from blockchain import blockexplorer, exchangerates
from django.conf import settings

api_code=settings.BTC_BLOCKCHAIN_API_CODE

class Blockchain:
    def __init__(self, address=None):
        self.address = address
        self.expiry_period = settings.BTC_PRICE_UPDATE_INTERVAL

    def generate_test_transaction(self, invoices):
        import time, random, binascii, os
        t = {
            'double_spend': False,
            'block_height': random.randint(100000, 900000),
            'time': int(time.time()),
            'relayed_by': '0.0.0.0',
            'hash': binascii.hexlify(os.urandom(16)),
            'tx_index': random.randint(100000000, 900000000),
            'ver': 1,
            'size': random.randint(100, 900),
            'inputs': [
                {
                    'prev_out': {
                        'n': 0,
                        'tx_index': random.randint(100000000, 900000000),
                        'value': float(invoices[0].crypto_due),
                        'type': None,
                        'script': "q1w2e3r4",
                    },
                    'script': "q1w2e3r4",
                    'sequence': 0
                }
            ],
            'out': [
                {
                    'n': 1,
                    'tx_index': random.randint(100000000, 900000000),
                    'spent': 0,
                    'addr': self.address,
                    'value': float(invoices[0].crypto_due),
                    'script': "abcd1234"
                }
            ]
        }
        transaction = blockexplorer.Transaction(t)
        return self.manage_transactions(invoices, [transaction])

    def get_transactions(self, invoices):
        tx_filter = blockexplorer.FilterType.ConfirmedOnly
        address = blockexplorer.get_address(self.address.public, filter=tx_filter, api_code=api_code)
        return self.manage_transactions(invoices, address.transactions)

    def manage_transactions(self, invoices, transactions):
        for t in transactions:
            timestamp = datetime.fromtimestamp(t.time)
            import pytz
            utc = pytz.UTC
            t.datetime= utc.localize(timestamp)
        txs = []
        for invoice in invoices:
            txs += [t for t in transactions if invoice.within_time_period(t.datetime)]
        for t in txs:
            t.total_received = sum([o.value for o in t.outputs if o.address == self.address])
        return transactions

    def convert_price_to_crypto(self, currency, price):
        return exchangerates.to_btc(currency, price)
