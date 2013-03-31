from django.conf import settings
from django.contrib.sites.models import RequestSite, Site
from django.http import HttpResponsePermanentRedirect, HttpResponse

from urlparse import urlunparse


class ValidateHostMiddleware(object):
    """
    Redirect every hostname which isn't the primary site to the primary site
    """
    def process_request(self, request):
        if settings.DEBUG:
            return
        request_site = RequestSite(request)
        primary_site = Site.objects.get_current()
        if request_site.domain != primary_site.domain:
            if request.path[0:7] == '/admin/':
                return
            if primary_site.domain == "example.com":
                return HttpResponse('improperly configured site<br><a href="/admin/sites/site/">config</a>')
            scheme = request.is_secure() and 'https' or 'http'
            url = urlunparse((scheme, primary_site.domain, request.path, None, request.META['QUERY_STRING'], None))
            return HttpResponsePermanentRedirect(url)  # don't loose link juice http://www.seomoz.org/learn-seo/redirection
