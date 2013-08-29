from urlparse import urlunparse

from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.http import HttpResponsePermanentRedirect


class EnforceHTTPSMiddleware(object):
    def process_request(self, request):
        if settings.DEBUG or request.is_secure():
            return
        url = request.build_absolute_uri(request.get_full_path())
        request_site = RequestSite(request)
        url = urlunparse(('https', request_site.domain, request.path, None, request.META['QUERY_STRING'], None))
        return HttpResponsePermanentRedirect(url)
