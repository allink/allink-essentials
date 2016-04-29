# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LegacyLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('old', models.CharField(unique=True, max_length=255, verbose_name='Old Link')),
                ('new', models.CharField(max_length=255, verbose_name='New Link')),
            ],
            options={
                'verbose_name': 'Legacy Link',
                'verbose_name_plural': 'Legacy Links',
            },
            bases=(models.Model,),
        ),
    ]
