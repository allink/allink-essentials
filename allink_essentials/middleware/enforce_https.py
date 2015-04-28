from urlparse import urlunparse

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class EnforceHTTPSMiddleware(object):
    def process_request(self, request):
        if settings.DEBUG or request.is_secure():
            return

        try:
            from django.contrib.sites.requests import RequestSite
        except ImportError:
            # deprecated since Django 1.7, works until 1.9,
            from django.contrib.sites.models import RequestSite

        request_site = RequestSite(request)
        url = urlunparse(('https', request_site.domain, request.path, None, request.META['QUERY_STRING'], None))
        return HttpResponsePermanentRedirect(url)
