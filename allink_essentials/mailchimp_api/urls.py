from django.conf.urls import patterns, url

from allink_essentials.mailchimp_api.views import SignupView

urlpatterns = patterns('',
    url(r'^$', SignupView.as_view(), name="mailchimp_singup"),
)
