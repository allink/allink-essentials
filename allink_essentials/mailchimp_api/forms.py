# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import get_language, ugettext_lazy as _

import mailchimp


class SignupForm(forms.Form):
    email = forms.EmailField(label=_(u'E-Mail'))
    language = forms.CharField(max_length=3, required=False)

    def save(self):
        email = self.cleaned_data['email']
        language = self.cleaned_data['language'] if 'language' in self.cleaned_data else get_language()

        list_id = settings.MAILCHIMP_LIST_ID
        double_optin = getattr(settings, 'MAILCHIMP_DOUBLE_OPTIN', True)
        send_welcome = getattr(settings, 'MAILCHIMP_SEND_WELCOME', True)
        additional_fields = getattr(settings, 'MAILCHIMP_ADDITIONAL_FIELDS', {})

        merge_vars = {'mc_language': language}
        merge_vars.update(additional_fields)  # adding extra fields with default value

        m = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
        m.lists.subscribe(list_id, {'email': email}, double_optin=double_optin, send_welcome=send_welcome, update_existing=True, merge_vars=merge_vars)
