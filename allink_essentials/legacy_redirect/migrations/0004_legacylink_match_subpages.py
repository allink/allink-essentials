# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy_redirect', '0003_auto_20160224_1216'),
    ]

    operations = [
        migrations.AddField(
            model_name='legacylink',
            name='match_subpages',
            field=models.BooleanField(default=False, help_text='If True, matches all subpages and redirects them to this link', verbose_name='Match subpages'),
            preserve_default=True,
        ),
    ]
