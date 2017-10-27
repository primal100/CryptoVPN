from django.db.models import DecimalField

class FiatField(DecimalField):
    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['max_digits'] = 8
        kwargs['decimal_places'] = 2
        super(FiatField, self).__init__(verbose_name, name, **kwargs)

class CryptoField(DecimalField):
    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['max_digits'] = 20
        kwargs['decimal_places'] = 20
        super(CryptoField, self).__init__(verbose_name, name, **kwargs)
