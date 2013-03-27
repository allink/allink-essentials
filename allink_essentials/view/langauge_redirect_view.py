from django.conf import settings
from django.views.generic import RedirectView


class FuzzyLanguageRedirectView(RedirectView):
    permanent = True  # don't loose link juice http://www.seomoz.org/learn-seo/redirection
    language_keys = dict(settings.LANGUAGES).keys()

    def get_redirect_url(self, **kwargs):
        """
        Return the URL redirect to. Keyword arguments from the
        URL pattern match generating the redirect request
        are provided as kwargs to this method.
        """
        if not 'HTTP_ACCEPT_LANGUAGE' in self.request.META.keys():
            return '/%s/' % settings.LANGUAGE_CODE
        browser_languages = self.request.META['HTTP_ACCEPT_LANGUAGE'].split(';')[0].split(',')
        # looking for exact match
        for language in browser_languages:
            if language in self.language_keys:
                return '/%s/' % language
        # looking for fuzzy match
        for language in browser_languages:
            for language_key in self.language_keys:
                if language[0:2] == language_key[0:2]:
                    return '/%s/' % language_key
        return '/%s/' % settings.LANGUAGE_CODE
