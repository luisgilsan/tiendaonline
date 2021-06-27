from django import forms
from .models import OrderItem,ColourVariation, Product, SizeVariation, Address
from django.contrib.auth.models import User
import environ
from django.shortcuts import get_object_or_404, reverse, redirect
import hashlib
from sequences import get_next_value
from datetime import datetime, timedelta
from django.conf import settings

env = environ.Env()
environ.Env.read_env()

class AddToCartForm(forms.ModelForm):
    # colour = forms.ModelChoiceField(queryset=ColourVariation.objects.none())
    # size = forms.ModelChoiceField(queryset=SizeVariation.objects.none())
    quantity = forms.IntegerField(min_value=1, label="Cantidad")

    class Meta:
        model = OrderItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop('product_id')
        super().__init__(*args,**kwargs)

    def clean(self):
        product_id = self.product_id
        product = Product.objects.get(id=self.product_id)
        quantity = self.cleaned_data['quantity']
        if product.stock < quantity:
            raise forms.ValidationError(f'El maximo stock disponible es {product.stock}')

class AddressForm(forms.Form):
    shipping_address_line_1 = forms.CharField(required=False, label="Dirección")
    shipping_address_line_2 = forms.CharField(required=False, label="Dirección 2 (opcional)")
    shipping_zip_code = forms.CharField(required=False, label="Ciudad")
    shipping_city = forms.CharField(required=False, label="Código postal")

    selected_shipping_address = forms.ModelChoiceField(
        Address.objects.none(),required=False
    )

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id') 
        super().__init__(*args, **kwargs)
        user = User.objects.get(id=user_id)
        print(user)
        shipping_address_qs = Address.objects.filter(
            user=user,
            address_type='S'
        )
        billing_address_qs = Address.objects.filter(
            user=user,
            address_type='B'
        )
        self.fields['selected_shipping_address'].queryset = shipping_address_qs

    def clean(self):
        data = self.cleaned_data
        selected_shipping_address = data.get('selected_shipping_address',None)
        if selected_shipping_address is None:
            if not data.get('shipping_address_line_1', None):
                self.add_error('shipping_address_line_1', "Por favor llene este campo")
            if not data.get('shipping_address_line_2', None):
                self.add_error('shipping_address_line_2', "Por favor llene este campo")
            if not data.get('shipping_zip_code', None):
                self.add_error('shipping_zip_code', "Por favor llene este campo")
            if not data.get('shipping_city', None):
                self.add_error('shipping_city', "Por favor llene este campo")
        selected_billing_address = data.get('selected_billing_address',None)
            
class PayUForm(forms.Form):

    merchantId = forms.IntegerField(min_value=1,max_value=999999999999)
    accountId = forms.IntegerField(min_value=1,max_value=999999)
    description = forms.CharField(max_length=255)
    referenceCode = forms.CharField(max_length=255)
    amount = forms.FloatField()
    tax = forms.FloatField()
    taxReturnBase = forms.IntegerField()
    currency = forms.CharField(max_length=3)
    signature = forms.CharField(max_length=255)
    test = forms.IntegerField(min_value=0,max_value=1)
    buyerEmail = forms.EmailField()
    responseUrl = forms.URLField()
    confirmationUrl = forms.URLField()

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        user_id = kwargs.pop('user_id')
        order = kwargs.pop('order')
        super().__init__(*args, **kwargs)
        if settings.PRODUCTION:
            self._prepare_production_form(order,user)
        else:
            self._prepare_test_form(order,user)

    def _prepare_test_form(self,order,user):
        code_test = str(get_next_value("sale_test_2"))
        merchantId = env('MERCHANID_SANDBOX')
        self.fields['merchantId'].initial = merchantId
        self.fields['accountId'].initial = env('ACCOUNTID_SANDBOX')
        self.fields['description'].initial = "Venta de prueba"
        self.fields['referenceCode'].initial = "RSS_TEST_" + str(datetime.now() - timedelta(hours=5)).replace(' ','-') + '_000' + code_test 
        self.fields['amount'].initial = order.get_raw_total()
        self.fields['tax'].initial = 0
        self.fields['taxReturnBase'].initial = 0
        self.fields['currency'].initial = 'COP'
        text_signature = env('API_KEY_SANDBOX') + '~' + merchantId + '~' + self.fields['referenceCode'].initial + \
            '~' + str(order.get_raw_total()) + '~' + 'COP'
        h = hashlib.md5()
        h.update(text_signature.encode('utf-8'))
        print('Cadena:  ' + text_signature)
        print(h.hexdigest())
        self.fields['signature'].initial = h.hexdigest()
        self.fields['test'].initial = 1
        self.fields['buyerEmail'].initial = user.email
        self.fields['responseUrl'].initial = 'http://luisgilsan.pythonanywhere.com/cart/response-payu/'
        self.fields['confirmationUrl'].initial = 'http://luisgilsan.pythonanywhere.com/cart/confirm-payu/'
        order.sended_signature = self.fields['signature'].initial
        order.sender_reference = self.fields['referenceCode'].initial
        order.user = user
        print('Useuario de la compra:')
        print(user.id)
        order.save()

    def _prepare_production_form(self,order,user):
        code_test = str(get_next_value("sale_2"))
        self.fields['merchantId'].initial = env('MERCHANID')
        self.fields['accountId'].initial = env('ACCOUNTID')
        self.fields['description'].initial = "Venta de productos RSS"
        self.fields['referenceCode'].initial = "RSS_TEST_" + str(datetime.now()).replace(' ','_') + '_000' + code_test 
        self.fields['amount'].initial = order.get_raw_total()
        self.fields['tax'].initial = 0
        self.fields['taxReturnBase'].initial = 0
        self.fields['currency'].initial = 'COP'
        text_signature = env('API_KEY') + '~' + env('MERCHANID') + '~' + self.fields['referenceCode'].initial + \
            '~' + str(order.get_raw_total()) + '~' + 'COP'
        h = hashlib.md5()
        h.update(text_signature.encode('utf-8'))
        print('Cadena:  ' + text_signature)
        print(h.hexdigest())

        self.fields['signature'].initial = h.hexdigest()
        self.fields['test'].initial = 0
        self.fields['buyerEmail'].initial = user.email
        self.fields['responseUrl'].initial = 'http://luisgilsan.pythonanywhere.com/cart/response-payu/'
        self.fields['confirmationUrl'].initial = 'http://luisgilsan.pythonanywhere.com/cart/confirm-payu/'
        order.sended_signature = self.fields['signature'].initial
        order.sender_reference = self.fields['referenceCode'].initial
        order.user = user
        order.save()