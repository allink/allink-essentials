# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import get_language, ugettext_lazy as _

from .config import MailChimpConfig
from helpers import list_members_put, get_status_if_new

config = MailChimpConfig()


class SignupForm(forms.Form):
    email = forms.EmailField(label=_(u'E-Mail'))
    language = forms.CharField(max_length=3, required=False)

    def save(self):
        email = self.cleaned_data['email']
        language = self.cleaned_data['language'] if 'language' in self.cleaned_data else get_language()

        data = {
            'email_address': email,
            'status': 'subscribed',
            'status_if_new': get_status_if_new(),
            'language': language
        }

        if config.merge_vars:
            data.update(config.merge_vars)

        if config.additional_fields:
            if not data.get('merge_fields'):
                data['merge_fields'] = {}
            data.get('merge_fields').update(config.additional_fields)

        list_members_put(data)
