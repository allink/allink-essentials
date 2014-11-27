from django import template
from django.conf import settings
from ..ecommerce import CanonicalOrder, plata_orderitem_to_canonical
from django.template.loader import render_to_string

register = template.Library()


class GanalyticsRenderNode(template.Node):
    def __init__(self, dont_track_page='False'):
        self.dont_track_page = template.Variable(dont_track_page)

    def render(self, context):
        try:
            dont_track_page = self.dont_track_page.resolve(context)
        except template.VariableDoesNotExist:
            dont_track_page = False
        analytics_id = getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
        return render_to_string('analytics/google-analytics.html', {
            'analytics_id': analytics_id,
            'trackPageview': not dont_track_page})


@register.tag
def ganalytics(parser, token):
    """
    Usage: {% ganalytics %} or {% ganalytics False %} if you wish to not track the page view and only load analytics code.
    You must define GOOGLE_ANALYTICS_ID = "UA-XXXXXXX-X" in your settings.py
    """
    args = token.split_contents()
    if len(args) == 2:
        return GanalyticsRenderNode(args[1])
    elif len(args) == 1:
        return GanalyticsRenderNode()
    else:
        raise template.TemplateSyntaxError("'ganalytics can't take more than one argument")


@register.inclusion_tag('analytics/google-tag-manager.html')
def google_tag_manager():
    return {'GOOGLE_TAG_MANAGER_ID': getattr(settings, 'GOOGLE_TAG_MANAGER_ID', None)}


@register.inclusion_tag('analytics/google-ecommerce.html')
def ecommerce_track(order):
    """ Usage: {% ecommerce_track order %} where `order` is a order object.
You must call this tag before and in conjunction with {% ganalytics %} in your template.
"""
    return {'order': CanonicalOrder(order.id, order.subtotal,
                                    orderitems=order.items.all(),
                                    converter=plata_orderitem_to_canonical,
                                    shipping_cost=order.shipping
                                    )}
