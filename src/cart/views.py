from django.views import generic
from .utils import get_or_set_order_session
from .models import Product, OrderItem, Address, Payment, Order, Category, Brand, PayuPayment
from .forms import AddToCartForm, AddressForm, PayUForm
from django.shortcuts import get_object_or_404, reverse, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.urls import reverse

import hashlib
import environ
import json
from datetime import datetime,timedelta
import logging
import requests

logging.getLogger().setLevel(logging.INFO)

env = environ.Env()
environ.Env.read_env()

URLPRODUCTION = "https://checkout.payulatam.com/ppp-web-gateway-payu"
URLTEST = "https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu"


class ProductListView(generic.ListView):
    template_name = 'cart/product_list.html'

    def get_queryset(self):
        qs = Product.objects.filter(active=True,stock__gte=1)
        category = self.request.GET.get('category',None)
        search = category = self.request.GET.get('search',None)
        print('POST realizado')
        print(search)
        brand = self.request.GET.get('brand',None)
        print('QS Prev')
        print(qs)
        if search:
            qs = qs.filter(Q(primary_category_id__name__icontains=search) |
                Q(title__icontains=search))
            pass
        elif category:
            qs = qs.filter(Q(primary_category_id__name=category))
        elif brand:
            qs = qs.filter(Q(brand_id__name=brand))
        print('QS End')
        print(qs)
        logging.warning("LOgging QS END...")
        return qs

    def get_context_data(self, **kwargs):
        context =  super(ProductListView, self).get_context_data(**kwargs)
        context.update({
            'categories' : Category.objects.all(),
            'brands' : Brand.objects.all()
        })
        return context
        
class ProductDetailView(generic.FormView):
    template_name = 'cart/product_detail.html'
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("cart:summary")

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView,self).get_form_kwargs()
        kwargs['product_id'] = self.get_object().id
        return kwargs

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()
        item_filter = order.items.filter(product=product,)

        if item_filter.exists():
            item = item_filter.first()
            item.quantity = int(form.cleaned_data['quantity'])
            item.save()
        else:
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()
        return super(ProductDetailView,self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView,self).get_context_data(**kwargs)
        context['product'] = self.get_object()
        return context

class CartView(generic.TemplateView):
    template_name = 'cart/cart.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CartView,self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

class OrderList(LoginRequiredMixin,generic.TemplateView):
    template_name = 'cart/order_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(OrderList,self).get_context_data(**kwargs)
        orders = Order.objects.filter(user_id=self.request.user,state__in=['pending','paid'])
        context["orders"] = orders
        return context

    def get_success_url(self):
        return reverse("cart:orders-list")

class OrderPendingView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'cart/order_pending.html'

    def get_context_data(self, *args, **kwargs):
        context = super(OrderPendingView,self).get_context_data(**kwargs)
        orders = Order.objects.filter(state__in=['pending','paid'])
        context["orders"] = orders
        return context

    def get_success_url(self):
        return reverse("cart:orders-pending")

class OrderDetail(LoginRequiredMixin,generic.TemplateView):
    template_name = 'cart/order_detail.html'

    def get_object(self):
        return get_object_or_404(Order, pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super(OrderDetail,self).get_form_kwargs()
        kwargs['order'] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrderDetail,self).get_context_data(**kwargs)
        context['order'] = self.get_object()
        return context

class IncreaseQuantityView(generic.View):

    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem,id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()
        return redirect('cart:summary')

class DiminishQuantityView(generic.View):
    
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem,id=kwargs['pk'])
        if order_item.quantity > 1:
            order_item.quantity -= 1
            order_item.save()
        else:
            order_item.delete()
        return redirect('cart:summary')

class DeleteOrderItemView(generic.View):
    
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem,id=kwargs['pk'])
        order_item.delete()
        return redirect('cart:summary')

class CheckoutView(LoginRequiredMixin,generic.FormView):
    template_name = 'cart/checkout.html'
    form_class = AddressForm

    def get_success_url(self):
        return reverse("cart:payment")

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        selected_shipping_address = form.cleaned_data.get('selected_shipping_address')

        if selected_shipping_address:
            order.shipping_address = selected_shipping_address
        else:
            address = Address.objects.create(
                address_type = 'S',
                user= self.request.user,
                address_line_1=form.cleaned_data['shipping_address_line_1'],
                address_line_2=form.cleaned_data['shipping_address_line_2'],
                zip_code=form.cleaned_data['shipping_zip_code'],
                city=form.cleaned_data['shipping_city'],
            )
            order.shipping_address = address
        order.save()
        messages.info(self.request, "Has llenado todo correctamente")
        return super(CheckoutView, self).form_valid(form)

    def get_form_kwargs(self):
        context = super(CheckoutView, self).get_form_kwargs()
        context['user_id'] = self.request.user.id
        return context

    def get_context_data(self, **kwargs):
        context = super(CheckoutView,self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

class PaymentView(LoginRequiredMixin,generic.FormView):
    template_name = 'cart/payment.html'
    form_class = PayUForm

    def get_success_url(self):
        return reverse('https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu')

    def get_form_kwargs(self):
        context = super(PaymentView, self).get_form_kwargs()
        context['user_id'] = self.request.user.id
        context['user'] = self.request.user
        context['order'] = get_or_set_order_session(self.request)        
        return context

    def get_context_data(self, **kwargs):
        context = super(PaymentView,self).get_context_data(**kwargs)
        urlpay = URLPRODUCTION if settings.PRODUCTION else URLTEST
        # urlpay = URLTEST
        context["PAYPAL_CLIENT_ID"] = settings.PAYPAL_CLIENT_ID
        context["CALLBACK_URL"] = reverse("cart:thanks-you")
        context["order"] = get_or_set_order_session(self.request)
        context["urlpay"] = urlpay
        return context

class ThankYouView(generic.TemplateView):
    template_name = 'cart/thanks.html'

class ConfirmOrderView(generic.View):
    def post(self, request, *args, **kwargs):
        order = get_or_set_order_session(request)
        body = json.loads(request.body)
        payment = Payment.objects.create(
            order=order,
            sucessful=True,
            raw_response = json.dumps(body),
            amount = float(body["purchase_units"][0]["amount"]["value"]),
            payment_method='Paypal'
        )
        order.ordered = True
        order.ordered_date = datetime.date.today()
        order.save()

        return JsonResponse({"data":"Success"})

    template_name = 'cart/thanks.html'

class ResponsePayUView(generic.View):
    template_name = 'cart/thanks.html'

    def get(self, request, *args, **kwargs):
        logging.warning("Receiving Payment...")
        if settings.PRODUCTION:
            order = self._validate_signature(request.GET)
        else:
            order = self._validate_signature_test(request.GET)
            logging.warning("Payment received...")
        if order:
            return redirect('cart:order-detail', pk=order.pk)
        else: 
            return redirect('cart:summary')
        # return redirect('cart:thanks-you')        

    def _validate_signature_test(self, request_dict):
        state_pol = request_dict.get('transactionState',False)
        value = request_dict.get('TX_VALUE',False)
        signature = request_dict.get('signature',False)
        reference_sale = request_dict.get('referenceCode',False)
        order = Order.objects.filter(sender_reference=str(reference_sale))
        if order:
            new_value = str(value)
            new_value = round(float(new_value), 1)
            payu_signature = env('API_KEY_SANDBOX') + '~' + env('MERCHANID_SANDBOX') + '~' + str(reference_sale) + \
                '~' + str(new_value) + '~' + 'COP' + '~' + str(state_pol)
            local_signature = hashlib.md5(payu_signature.encode('utf-8')).hexdigest()
            if local_signature == signature and str(state_pol) == '4':
                logging.info("Validation was successfull. Signature received: %s" % (signature,))
                order = self._create_received_payment(request_dict)
                return order
            else:
                logging.info("Payment was not approved.")
        else:
            logging.info("Sell order not found.")
        return False

    def _validate_signature(self, request_dict):
        state_pol = request_dict.get('transactionState',False)
        value = request_dict.get('TX_VALUE',False)
        signature = request_dict.get('signature',False)
        reference_sale = request_dict.get('referenceCode',False)
        order = Order.objects.filter(sender_reference=str(reference_sale))
        if order:
            new_value = str(value)
            new_value = round(float(new_value), 1)
            payu_signature = env('API_KEY') + '~' + env('MERCHANID') + '~' + str(reference_sale) + \
                '~' + str(new_value) + '~' + 'COP' + '~' + str(state_pol)
            local_signature = hashlib.md5(payu_signature.encode('utf-8')).hexdigest()
            if local_signature == signature and str(state_pol) == '4':
                logging.info("Validation was successfull. Signature received: %s" % (signature,))
                self._create_received_payment(request_dict)
            else:
                logging.info("Payment was not approved.")
        else:
            logging.info("Sell order not found.")

    def _create_received_payment(self,request_dict):
        reference_sale = request_dict.get('referenceCode',False)
        order = Order.objects.filter(sender_reference=str(reference_sale))
        if order:
            order = order.first()
            if not order.already_payment():
                state_pol = request_dict.get('transactionState',False)
                value = request_dict.get('TX_VALUE',False)
                response_code_pol = request_dict.get('polResponseCode',False)
                payment_method_type = request_dict.get('polPaymentMethodType',False)
                response_message_pol = request_dict.get('lapResponseCode',False)
                payment_method_id = request_dict.get('polPaymentMethodType',False)
                logging.info("Payment_method_id: %s" % (payment_method_id,))
                payment = PayuPayment(
                    transaction_state=state_pol,
                    pol_response_code=response_code_pol,
                    pol_payment_method_type=payment_method_type,
                    payment_method_id=int(payment_method_id),
                    response_message_pol=response_message_pol,
                    value=value,
                    reponse_method='response',
                    payment_date=datetime.now() - timedelta(hours=5))
                payment.save()
                order.payu_payment_id = payment
                order.save()
                order.pay()
                logging.info("payment stored in database: %s. Order closed %s" % (payment.name, order.id))
            else:
                logging.info("Order %s has already been paid." % (order.id))
            # return redirect('cart:order-detail',args={'pk':order.pk}) 
            return order
        else:
            return False

class ConfirmPayUView(generic.View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ConfirmPayUView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logging.info("Confirming payment...")
        self._validate_signature(request.POST)
        logging.info("Payment confirmed...")
        return HttpResponse("Payment confirmed...")

    def _validate_signature(self, request_dict):
        print('recuperando datos..')
        state_pol = request_dict.get('state_pol',False)
        value = request_dict.get('value',False)
        signature = request_dict.get('sign',False)
        reference_sale = request_dict.get('reference_sale',False)
        print('busca pedidos..')
        order = Order.objects.filter(sender_reference=str(reference_sale))
        
        if order:
            print('Pedido encontrads..')
            new_value = str(value)
            new_value = round(float(new_value), 1)
            payu_signature = env('API_KEY') + '~' + env('MERCHANID') + '~' + str(reference_sale) + \
                '~' + str(new_value) + '~' + 'COP' + '~' + str(state_pol)
            local_signature = hashlib.md5(payu_signature.encode('utf-8')).hexdigest()
            print('Signature generado..')
            if local_signature == signature and str(state_pol) == '4':
                logging.info("Validation was successfull. Signature received: %s" % (signature,))
                self._create_confirmed_payment(request_dict)
            else:
                print('No validado...')
                logging.info("Payment was not approved.")
        else:
            print('Pedido no encontrado..')
            logging.info("Sell order not found.")

    def _create_confirmed_payment(self,request_dict):
        reference_sale = request_dict.get('reference_sale',False)
        order = Order.objects.filter(sender_reference=str(reference_sale))
        if order:
            order = order[0]
            state_pol = request_dict.get('state_pol',False)
            value = request_dict.get('value',False)
            response_code_pol = request_dict.get('response_code_pol',False)
            payment_method_type = request_dict.get('payment_method_type',False)
            response_message_pol = request_dict.get('response_message_pol',False)
            payment_method_id = request_dict.get('payment_method_id',False)
            logging.info("Payment_method_id: %s" % (payment_method_id,))
            payment = PayuPayment(
                transaction_state=state_pol,
                pol_response_code=response_code_pol,
                pol_payment_method_type=payment_method_type,
                payment_method_id=int(payment_method_id),
                response_message_pol=response_message_pol,
                value=value,
                reponse_method='confirm',
                payment_date=datetime.now() - timedelta(hours=5))
            payment.save()
            order.payu_payment_id = payment
            order.save()
            order.pay()
            logging.info("payment stored in database: %s. Order closed %s" % (payment.name, order.id))

class DoPaymentView(LoginRequiredMixin,generic.View):

    def post(self, request, *args, **kwargs):
        logging.info("Preparing payu Data ...")
        order_id = self.kwargs.get('pk',False)
        logging.info('Order ID')
        logging.info(str(order_id))
        order = Order.objects.filter(pk=order_id)
        if order:
            logging.info("Order Found ...")
            data = {'test':'test'}
            url = 'https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu'
            redirect('https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu', pk=order.pk)
            payu_response = requests.post(url, data=data)
            return HttpResponse(payu_response.text)
        else:
            logging.info('No redireccionado')
            return HttpResponse('No redireccionado')