from import_export import resources, fields

from django.utils.translation import ugettext_lazy as _

from allink_essentials.legacy_redirect.models import LegacyLink


class LegacyLinkResource(resources.ModelResource):
    old = fields.Field(column_name=_('Zielseite'), attribute='old')

    class Meta:
        model = LegacyLink
        fields = ['old']
        import_id_fields = ['old']
        skip_unchanged = True

    def skip_row(self, instance, original):
        out = super(LegacyLinkResource, self).skip_row(instance, original)
        # skip urls which we never want to be redirected
        if not out and instance.old in [u'(not set)', u'/']:
            return True
        return out
