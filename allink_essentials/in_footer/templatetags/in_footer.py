from django import template
from django.utils import translation

from feincms.module.page.models import Page
from feincms.utils.templatetags import SimpleAssignmentNodeWithVarAndArgs
from feincms.utils.templatetags import do_simple_assignment_node_with_var_and_args_helper

register = template.Library()


class FooterNavigationNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    {% load footer_tags %}
    {% footer_navigation for feincms_page as footer_pages %}
    {% for p in footer_pages %}
        <a href="{{p.get_absolute_url}}">{{p.title}}</a>{% if not forloop.last %} |{% endif %}
    {% endfor %}
    """
    def what(self, page, args, default=None):
        return Page.objects.active().filter(in_footer=True).filter(language=translation.get_language())
        
register.tag('footer_navigation', do_simple_assignment_node_with_var_and_args_helper(FooterNavigationNode))
