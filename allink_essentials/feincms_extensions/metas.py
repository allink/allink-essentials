from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms._internal import monkeypatch_property


def register(cls, admin_cls):
    cls.add_to_class('_meta_title', models.CharField(_('Meta Title'), max_length=69, blank=True, help_text=_('Meta title for browser window and search engines. Same as title by default. Recommended structure "Primary Keyword - Secondary Keyword | Brand Name" (max. 69).')))
    cls.add_to_class('meta_description', models.TextField(_('Meta Description'), max_length=139, blank=True, help_text=_('Meta description for search engines (max 139).')))
    cls.add_to_class('_nav_title', models.CharField(_('Navigation Title'), max_length=100, blank=True, help_text=_('Used in navigation. Same as title by default.')))

    @monkeypatch_property(cls)
    def meta_title(self):
        if self._meta_title:
            return self._meta_title
        return self.title

    @monkeypatch_property(cls)
    def nav_title(self):
        if self._nav_title:
            return self._nav_title
        return self.title

    if admin_cls:
        admin_cls.search_fields.extend(['_meta_title', 'meta_description', '_nav_title'])
        admin_cls.add_extension_options(_('Meta Fields'), {
            'fields': ('_meta_title', 'meta_description', '_nav_title',),
        })
