from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms.admin import tree_editor


class Extension(extensions.Extension):
    def handle_model(self):

        self.model.add_to_class('in_footer', models.BooleanField(_('In footer'), default=False, help_text=_('This displays the page in the footer navigation.')))

    def handle_modeladmin(self, modeladmin):
        setattr(type(modeladmin), 'in_footer_toggle', tree_editor.ajax_editable_boolean('in_footer', _('in footer')))
        modeladmin.list_display.insert(3, 'in_footer_toggle')
