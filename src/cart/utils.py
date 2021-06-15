from .models import Order

def get_or_set_order_session(request):
    order_id = request.session.get('order_id', None)
    order = False
    if order_id is None:
        order = Order()
        order.save()
        request.session['order_id'] = order.id
    else: 
        order = Order.objects.filter(id=order_id, ordered=False,state='draft')
        print('Orden en prev')
        print(order)
        print(len(order))
        if len(order) == 0:
            order = Order()
            order.save()
            request.session['order_id'] = order.id
            print('Envontro en cath:')
            print(order)
            return order

    # if request.user.is_authenticated and order.user is None:
    #     order.user= request.user
    #     order.save()
    if order:
        return order.first()
    return order