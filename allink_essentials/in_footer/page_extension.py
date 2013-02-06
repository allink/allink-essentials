"""
Somtimes you need a in_footer Property
This extension lets you do that.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.admin import tree_editor


def register(cls, admin_cls):
    cls.add_to_class('in_footer', models.BooleanField(_('In footer'), default=False,
        help_text=_('This displays the page in the footer navigation.')))

    setattr(admin_cls, 'in_footer_toggle', tree_editor.ajax_editable_boolean('in_footer', _('in footer')))
    admin_cls.list_display.insert(3, 'in_footer_toggle')
