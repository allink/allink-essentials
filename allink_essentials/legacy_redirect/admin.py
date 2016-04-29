# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ImportMixin
from import_export.formats import base_formats

from allink_essentials.legacy_redirect.utils import base_url

from allink_essentials.legacy_redirect.forms import LegacyChangeAdminForm
from allink_essentials.legacy_redirect.models import LegacyLink
from allink_essentials.legacy_redirect.resources import LegacyLinkResource


class LegacyLinkAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ['old', 'new', 'overwrite', 'active', 'match_subpages', 'last_test_result', 'last_test_date', 'manual_test']
    list_editable = ['new', 'overwrite', 'active', 'match_subpages']
    readonly_fields = ['last_test_result', 'last_test_date']
    form = LegacyChangeAdminForm
    resource_class = LegacyLinkResource
    actions = ['auto_test']

    def get_changelist_form(self, request, **kwargs):
        kwargs.setdefault('form', LegacyChangeAdminForm)
        return super(LegacyLinkAdmin, self).get_changelist_form(request, **kwargs)

    def get_import_formats(self):
        """ We only allow csv for
            Google Analytics files
        """
        return [base_formats.CSV]

    def auto_test(self, request, queryset):
        for obj in queryset:
            obj.test_redirect(request)
    auto_test.short_description = _(u'Test redirect')

    def manual_test(self, obj):
        link = base_url() + obj.old
        return format_html('<a class="button" href="%s" target="_blank">Link</a>' % link)
    manual_test.short_description = _(u'Manual testing')

admin.site.register(LegacyLink, LegacyLinkAdmin)
