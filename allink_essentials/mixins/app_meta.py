from django.db import models
from django.core.validators import MaxLengthValidator
from django.utils.translation import ugettext_lazy as _


class AppMeta(models.Model):
    title_tag = models.CharField(_('Title Tag'), max_length=69, blank=True, help_text=_('Title for browser window and search engines. Same as title by default. Recommended structure "Primary Keyword - Secondary Keyword" (max. 69). Your brand name will be added by default.'))
    meta_description = models.TextField(_('Meta Description'), max_length=139, blank=True, help_text=_('Meta description for search engines (max 139).'), validators=[MaxLengthValidator(139)])
    og_image = models.ImageField(_('og:image'), blank=True, null=True, upload_to='og_images', help_text=_('Preview image when sharing in social networks.'))

    class Meta:
        abstract = True
