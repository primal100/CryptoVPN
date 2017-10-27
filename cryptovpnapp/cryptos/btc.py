from datetime import datetime
from blockchain import blockexplorer, exchangerates
from django.conf import settings

api_code=settings.BTC_WALLET_SETTINGS['api_code']

class Blockchain:
    def __init__(self, address=None):
        self.address = address
        self.expiry_period = settings.BTC_PRICE_UPDATE_INTERVAL

    def generate_test_transaction(self, invoice):
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

                }
            ],
            'out': [
                {

                }
            ]
        }
        transaction = blockexplorer.Transaction(t)
        return [transaction]

    def get_transactions(self, period):
        tx_filter = blockexplorer.FilterType.ConfirmedOnly
        address = blockexplorer.get_address(self.address.public, filter=tx_filter, api_code=api_code)
        transactions = address.transactions
        for transaction in transactions:
            transaction.datetime = datetime.fromtimestamp(transaction.time)
        now = datetime.now()
        if period:
            transactions = [transaction for transaction in transactions if (now - transaction.date) > period]
        for transaction in transactions:
            transaction.total_value = sum([i.value for i in transaction.outputs])
            transaction.fee = sum([i.value for i in transaction.inputs]) - transaction.total_value
        return transactions

    def convert_price_to_crypto(self, currency, price):
        return exchangerates.to_btc(currency, price)
