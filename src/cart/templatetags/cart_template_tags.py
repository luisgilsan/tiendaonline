from django import template
from cart.utils import get_or_set_order_session

register = template.Library()

@register.filter
def cart_item_count(request):
    order = get_or_set_order_session(request)
    if order:
        if order.state in ['pending', 'paid']:
            return 0
        count = order.items.count()
        return order.items.count()
    else:
        return 0