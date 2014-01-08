from __future__ import absolute_import, unicode_literals

from django.db import models
from django.core.validators import MaxLengthValidator
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms._internal import monkeypatch_property


class Extension(extensions.Extension):
    def handle_model(self):

        self.model.add_to_class('_title_tag', models.CharField(_('Title Tag'), max_length=69, blank=True, help_text=_('Title for browser window and search engines. Same as title by default. Recommended structure "Primary Keyword - Secondary Keyword" (max. 69). Your brand name will be added by default.')))
        self.model.add_to_class('meta_description', models.TextField(_('Meta Description'), max_length=139, blank=True, help_text=_('Meta description for search engines (max 139).'), validators=[MaxLengthValidator(139)]))
        self.model.add_to_class('og_image', models.ImageField(_('og:image'), blank=True, null=True, upload_to='og_images', help_text=_('Preview image when sharing in social networks.')))

        @monkeypatch_property(self.model)
        def title_tag(self):
            if self._title_tag:
                return self._title_tag
            return self.title

    def handle_modeladmin(self, modeladmin):
        modeladmin.search_fields.extend(['_title_tag', 'meta_description'])
        modeladmin.add_extension_options(_('Meta Fields'), {
            'fields': ('_title_tag', 'meta_description', 'og_image',),
        })
