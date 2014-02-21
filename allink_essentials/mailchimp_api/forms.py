# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import get_language, ugettext_lazy as _

import mailchimp


class SignupForm(forms.Form):
    email = forms.EmailField(label=_(u'E-Mail'))

    def save(self):
        email = self.cleaned_data['email']

        list_id = settings.MAILCHIMP_LIST_ID
        double_optin = getattr(settings, 'MAILCHIMP_DOUBLE_OPTIN', True)
        send_welcome = getattr(settings, 'MAILCHIMP_SEND_WELCOME', True)

        m = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
        m.lists.subscribe(list_id, {'email': email}, double_optin=double_optin, send_welcome=send_welcome, update_existing=True, merge_vars={'mc_language': get_language()})
