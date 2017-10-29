from datetime import datetime
from blockchain import blockexplorer, exchangerates
from django.conf import settings

api_code=settings.BTC_WALLET_SETTINGS['api_code']

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
                    'value': invoices[0].crypto_due
                }
            ],
            'out': [
                {
                    'value': invoices[0].crypto_due * 0.999
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
            t.datetime = datetime.fromtimestamp(t.time)
        txs = []
        for invoice in invoices:
            txs += [t for t in transactions if invoice.within_time_period(t.time)]
        for t in txs:
            t.total_value = sum([i.value for i in t.outputs])
            t.fee = sum([i.value for i in t.inputs]) - t.total_value
        return transactions

    def convert_price_to_crypto(self, currency, price):
        return exchangerates.to_btc(currency, price)
