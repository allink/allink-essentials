from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):

        self.model.add_to_class('in_footer', models.BooleanField(_('In footer'), default=False, help_text=_('This displays the page in the footer navigation.')))

    def handle_modeladmin(self, modeladmin):
        modeladmin.list_display.extend(['in_footer'])
        modeladmin.list_editable += ('in_footer',)
        modeladmin.add_extension_options(_('Footer Navigation'), {
            'fields': ('in_footer',),
        })
