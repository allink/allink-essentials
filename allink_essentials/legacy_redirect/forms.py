# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from allink_essentials.legacy_redirect.models import LegacyLink
from allink_essentials.legacy_redirect.utils import choices_from_sitemaps


class LegacyChangeAdminForm(forms.ModelForm):
    new = forms.ChoiceField(label=_('New Link'), choices=[], required=False)

    class Meta:
        model = LegacyLink
        fields = ['old', 'new', 'overwrite', 'active', 'match_subpages']

    def __init__(self, *args, **kwargs):
        super(LegacyChangeAdminForm, self).__init__(*args, **kwargs)
        self.fields['new'].choices = choices_from_sitemaps()
