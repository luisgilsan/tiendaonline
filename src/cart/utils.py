from .models import Order

def get_or_set_order_session(request):
    order_id = request.session.get('order_id', None)
    order = False
    if order_id is None:
        order = Order()
        order.save()
        request.session['order_id'] = order.id
        print('Orden generada')
    else: 
        order = Order.objects.filter(id=order_id, ordered=False,state='draft')            
        print('Orden econtrada')
        print(order)
        print(len(order))
        if len(order) == 0:
            order = Order()
            order.save()
            request.session['order_id'] = order.id
            print('Envontro en cath:')
            print(order)
            return order
        else:
            order = order.first()
    print('Tipo de dato')
    print(str(type(order)))
    return order