# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy_redirect', '0004_legacylink_match_subpages'),
    ]

    operations = [
        migrations.AddField(
            model_name='legacylink',
            name='overwrite',
            field=models.CharField(help_text="Overwrites 'New Link', use for special urls that are not listed there", max_length=255, null=True, verbose_name='Overwrite Link', blank=True),
            preserve_default=True,
        ),
    ]
