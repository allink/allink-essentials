from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class LegacyRedirectConfig(AppConfig):
    name = 'allink_essentials.legacy_redirect'
    verbose_name = _('Legacy Redirect')
