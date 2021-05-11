from django.views import generic
from .utils import get_or_set_order_session
from .models import Product, OrderItem, Address, Payment, Order, Category, Brand
from .forms import AddToCartForm, AddressForm, PayUForm
from django.shortcuts import get_object_or_404, reverse, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
import json
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

class ProductListView(generic.ListView):
    template_name = 'cart/product_list.html'

    def get_queryset(self):
        qs = Product.objects.all()
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
        selected_billing_address = form.cleaned_data.get('selected_billing_address')

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
        if selected_billing_address:
            order.billing_address = selected_billing_address
        else:
            address = Address.objects.create(
                address_type = 'B',
                user= self.request.user,
                address_line_1=form.cleaned_data['billing_address_line_1'],
                address_line_2=form.cleaned_data['billing_address_line_2'],
                zip_code=form.cleaned_data['billing_zip_code'],
                city=form.cleaned_data['billing_city'],
            )
            order.billing_address = address
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
        context['order'] = get_or_set_order_session(self.request)
        print('Contexto de la vista')
        print(self.request.user.id)
        
        return context

    def get_context_data(self, **kwargs):
        context = super(PaymentView,self).get_context_data(**kwargs)
        context["PAYPAL_CLIENT_ID"] = settings.PAYPAL_CLIENT_ID
        context["CALLBACK_URL"] = reverse("cart:thanks-you")
        context["order"] = get_or_set_order_session(self.request)
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

class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'order.html'
    queryset = Order.objects.all()
    context_object_name = 'order'