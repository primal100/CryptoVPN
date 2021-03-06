# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-29 11:40
from __future__ import unicode_literals

from django.db import migrations

def add_addresses(apps, schema_editor):
    addresses = ["1NjYHJvQ5eAeZq6Dmkj6jbVtqQrsHPkthJ", "1DpAEKxUaCuq4M3LPQxWfZ5Wm8AAZ64nxc",
                 "19BMbDAbzoCa7Fzyaxno9paDkJ8gx2jEeJ", "151Ea1GmEeF7rhUrnLEo16cSAGUwxRw37Z",
                 "18J98jKJi8mcPYnvWqYc9aWHkvDSujXz46", "13EyhYxeqZtMDVbSVmoFTG3THqePVGd2pz",
                 "1BcLNfFtG3M4GsDbQVw6fRnJFBRWRVb4rR", "1F3EPSeriw6b71oZqmZDeQRZXWz9ssumUY",
                 "1Q61E57zKgAbizMyirUiSMCHrv1AWBxZPv", "18kNKB4RC9aLkxCbNQkRRq7SgxSUjmS9NT",
                 "1BPeH4Rf2U7KCXf7jxXH3oCJ2uZUQM1heL", "1MKoftr1cbb6JW2Y6MLq3L1rxzvMt7zkJr",
                 "1K8e2LRd895N9B5spYJyXW21jp4FK2EqVp", "13i1QthcaSpW73Djj4VnvS2iaZwcD84qC7",
                 "1FRJsTJH5EBPRXa2DACpMcdVCV9uapgCiC", "1PsXdVoXiGzdyAEHN4RKS2sCgefrax7bNJ",
                 "16ivzqbMBUzW8ZYTMz5fCGmFYNDgKyAQ7", "1FbBHzdBACDEQ5ijhkesujNRA6zT37i3Mx",
                 "19G6Qa3um1xagfCWu1VrDMLTKikFftjuYn", "1J3GPLzWoW6o6gMEZbXC1aSkp3cAqZF9QV"]
    Address = apps.get_model('cryptovpnapp', 'Address')
    address_instances = [Address(public=a, test_address=True, coin="BTC") for a in addresses]
    Address.objects.bulk_create(address_instances)

class Migration(migrations.Migration):

    dependencies = [
        ('cryptovpnapp', '0003_auto_20171028_1511'),
    ]

    operations = [
        migrations.RunPython(add_addresses)
    ]
