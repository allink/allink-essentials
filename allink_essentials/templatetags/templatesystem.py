from django import template
from django.template import Template, Context

register = template.Library()


@register.simple_tag(takes_context=True)
def conditional_include(context, region, is_editor=False):
    """
        usage in moduletemplates from allink boilerplate.
        {%% load templatesystem %%}
        {%% conditional_include 'REGION_NAME' %%}
        REGION_NAME could be 'footer' for example
    """
    if 'is_editor' not in context:
        return Template('{%% include "partials/%s.html" %%}' % region).render(Context(context))
