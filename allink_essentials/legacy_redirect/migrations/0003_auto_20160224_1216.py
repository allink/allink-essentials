# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy_redirect', '0002_legacylink_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='legacylink',
            name='last_test_date',
            field=models.DateTimeField(null=True, verbose_name='Date of last test', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='legacylink',
            name='last_test_result',
            field=models.NullBooleanField(default=None, help_text='Was the last automatic test successfull? (True = Yes, False = No, None = Not yet tested)', verbose_name='Result of last test'),
            preserve_default=True,
        ),
    ]
