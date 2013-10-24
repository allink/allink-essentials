class CanonicalOrder(object):
    """ A generalized order model used for ecommerce tracking.
        Required args are expected to be non-empty for successful tracking.

        orderitems
            list of items in your order model

        converter
            function returning a CanonicalOrder.OrderItem object from an item in orderitems list
    """
    def __init__(self, id, subtotal, orderitems, converter, affiliation='', tax='', shipping_cost='', city='', state='', country=''):
        super(CanonicalOrder, self).__init__()
        self.__dict__.update(locals())  # set args as ivars
        self.items = [converter(i) for i in orderitems]

    class OrderItem(object):
        """Canonical OrderItem model"""
        def __init__(self, sku, unit_price, quantity, name='', category=''):
            super(self.__class__, self).__init__()
            self.__dict__.update(locals())


def plata_orderitem_to_canonical(item):
    """ Converts a plata.shop.order_model.orderitem object to a CanonicalOrder.OrderItem object by defining an attribute mapping. """
    return CanonicalOrder.OrderItem(sku=item.variation.sku,
                                    name=item.variation,
                                    unit_price=item.unit_price,
                                    quantity=item.quantity,
                                    )
