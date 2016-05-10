# -*- coding: utf-8 -*-

from django import http
from django.template import Context, Engine, TemplateDoesNotExist, loader
from django.utils import six
from django.utils.translation import get_language
from feincms.module.page.models import Page


# this method is for django version >= 1.9
# for older versions use view.page_not_found

def page_not_found(request, exception, template_name='404.html'):
    """
    Standard 404 view + feincms_page in context. Like this we can display
    navigations in 404 page, without using the add_page_if_missing middleware.
    We don't want to use the middleware, cause the page preview function,
    doe't work correctly with it.
    """
    exception_repr = exception.__class__.__name__
    # Try to get an "interesting" exception message, if any (and not the ugly
    # Resolver404 dictionary)
    try:
        message = exception.args[0]
    except (AttributeError, IndexError):
        pass
    else:
        if isinstance(message, six.text_type):
            exception_repr = message
    try:
        feincms_page = Page.objects.active().filter(language=get_language())[0]
    except IndexError:
        feincms_page = None
    context = {
        'request_path': request.path,
        'exception': exception_repr,
        'feincms_page': feincms_page
    }
    request._feincms_page = feincms_page
    try:
        template = loader.get_template(template_name)
        body = template.render(context, request)
        content_type = None             # Django will use DEFAULT_CONTENT_TYPE
    except TemplateDoesNotExist:
        template = Engine().from_string(
            '<h1>Not Found</h1>'
            '<p>The requested URL {{ request_path }} was not found on this server.</p>')
        body = template.render(Context(context))
        content_type = 'text/html'
    return http.HttpResponseNotFound(body, content_type=content_type)
