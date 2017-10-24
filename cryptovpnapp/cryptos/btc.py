from datetime import datetime
from blockchain import blockexplorer, exchangerates, util, wallet, exceptions
from django.conf import settings
import urllib.request
from urllib.error import HTTPError
import json

btc_wallet = wallet.Wallet(**settings.BTC_WALLET_SETTINGS)
api_code=settings.BTC_WALLET_SETTINGS['api_code']
callback_url = settings.BTC_CALLBACK_URL
confs_before_notification = settings.BTC_CONFS_BEFORE_NOTIFICATION

def to_fiat_with_timestamp(ccy, value, timestamp, api_code=None):
    """Call the 'frombtc' method and convert x value in the provided currency to BTC.

    :param str ccy: currency code
    :param float value: BTC value to convert
    :param float timestamp: Timestamp in seconds since the epoch
    :param str api_code: Blockchain.info API code
    :return: the value in fiat currency
    """
    res = 'frombtc?currency={0}&value={1}&time={2}&textual=false&nosavecurrency=true'.format(ccy, value*100000000, timestamp)
    if api_code is not None:
        res += '&api_code=' + api_code
    return float(util.call_api(res))


class CoinWallet:
    def __init__(self, address=None):
        self.address = address

    def get_transactions(self, period=None):
        tx_filter = blockexplorer.FilterType.ConfirmedOnly
        address = blockexplorer.get_address(self.address.public, filter=tx_filter, api_code=api_code)
        transactions = address.transactions
        for transaction in transactions:
            transaction.datetime = datetime.fromtimestamp(transaction.time)
        now = datetime.now()
        period = self.address.user.subscription_period
        if period:
            transactions = [transaction for transaction in transactions if (now - transaction.date) > period]
        for transaction in transactions:
            transaction.total_value = sum([i.value for i in transaction.inputs])
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

class Exchange:
    def get_current_price(self):
        return 0