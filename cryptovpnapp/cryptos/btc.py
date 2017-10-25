from datetime import datetime
from blockchain import blockexplorer, exchangerates, wallet
from django.conf import settings

btc_wallet = wallet.Wallet(**settings.BTC_WALLET_SETTINGS)
api_code=settings.BTC_WALLET_SETTINGS['api_code']

class CoinWallet:
    def __init__(self, address=None):
        self.address = address
        self.expiry_period = settings.BTC_PRICE_UPDATE_INTERVAL

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
            transaction.total_value = sum([i.value for i in transaction.inputs]) - sum([i.value for i in transaction.outputs])
        return transactions

    @property
    def wallet_address(self):
        return btc_wallet.get_address(self.address.public)

    @property
    def balance(self):
        return self.wallet_address.balance

    def new_address(self, username):
        return btc_wallet.new_address(label=username)

    def distribute_coins(self):
        if self.address:
            from_address = self.address.public
        else:
            from_address = None
        amount = self.balance()
        send_addresses = settings.BTC_STORE_ADDRESSES
        recipients = {address:fraction*amount for address,fraction in send_addresses.items()}
        return btc_wallet.send_many(recipients, from_address=from_address)

    def list_addresses(self):
        return btc_wallet.list_addresses()

    def convert_price_to_crypto(self, currency, price):
        return exchangerates.to_btc(currency, price)
