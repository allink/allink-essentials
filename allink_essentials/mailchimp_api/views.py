from django.conf import settings
from django.http import HttpResponse
from django.utils.module_loading import import_by_path
from django.views.generic import FormView

from allink_essentials.mailchimp_api.forms import SignupForm


class SignupView(FormView):
    form_class = SignupForm
    template_name = 'mailchimp_api/signup_form.html'

    def __init__(self, **kwargs):
        super(SignupView, self).__init__(**kwargs)
        if getattr(settings, 'MAILCHIMP_SIGNUP_FORM', False):
            self.form_class = import_by_path(settings.MAILCHIMP_SIGNUP_FORM)

    def form_valid(self, form):
        form.save()
        return HttpResponse('ok')
