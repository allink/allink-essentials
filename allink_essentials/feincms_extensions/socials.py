from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms._internal import monkeypatch_property


def register(cls, admin_cls):
    cls.add_to_class('_og_title', models.CharField(_('Title'), max_length=69, blank=True, help_text=_('Used for og:title. Same as title by default.')))
    cls.add_to_class('_og_description', models.TextField(_('Description'), blank=True, help_text=_('Used for og:description. Same as meta description by default.')))

    @monkeypatch_property(cls)
    def og_title(self):
        if self._og_title:
            return self._og_title
        return self.meta_title

    @monkeypatch_property(cls)
    def og_description(self):
        if self._og_description:
            return self._og_description
        return self.meta_description

    if admin_cls:
        admin_cls.search_fields.extend(['_og_title', '_og_description'])
        admin_cls.add_extension_options(_('Social Fields'), {
            'fields': ('_og_title', '_og_description',),
            'classes': ('collapse',),
        })
