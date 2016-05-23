from django import template
from django.utils import translation

from feincms.module.page.models import Page
from feincms.utils.templatetags import SimpleAssignmentNodeWithVarAndArgs
from feincms.utils.templatetags import do_simple_assignment_node_with_var_and_args_helper

register = template.Library()


class FooterNavigationNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    {% load in_footer %}
    {% footer_navigation for feincms_page as footer_pages %}
    {% for p in footer_pages %}
        <a href="{{p.get_absolute_url}}">{{p.title}}</a>{% if not forloop.last %} |{% endif %}
    {% endfor %}
    """
    def what(self, page, args, default=None):
        queryset = Page.objects.active().filter(in_footer=True)
        return queryset.filter(language=translation.get_language()) if 'language' in [f.name for f in Page._meta.fields] else queryset

register.tag('footer_navigation', do_simple_assignment_node_with_var_and_args_helper(FooterNavigationNode))


@register.simple_tag(name="footer_pages")
def in_footer():
    queryset = Page.objects.active().filter(in_footer=True)
    return queryset.filter(language=translation.get_language()) if 'language' in [f.name for f in Page._meta.fields] else queryset
