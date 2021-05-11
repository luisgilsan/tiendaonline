from django import forms
from .models import OrderItem,ColourVariation, Product, SizeVariation, Address
from django.contrib.auth.models import User
import environ
from django.shortcuts import get_object_or_404, reverse, redirect
import hashlib
from sequences import get_next_value

env = environ.Env()
environ.Env.read_env()

class AddToCartForm(forms.ModelForm):
    # colour = forms.ModelChoiceField(queryset=ColourVariation.objects.none())
    # size = forms.ModelChoiceField(queryset=SizeVariation.objects.none())
    quantity = forms.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['quantity']

    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop('product_id')
        # product = Product.objects.get(id=self.product_id)
        super().__init__(*args,**kwargs)
        # self.fields['colour'].queryset = product.available_colours.all()
        # self.fields['size'].queryset = product.available_sizes.all()

    def clean(self):
        product_id = self.product_id
        product = Product.objects.get(id=self.product_id)
        quantity = self.cleaned_data['quantity']
        if product.stock < quantity:
            raise forms.ValidationError(f'El maximo stock disponible es {product.stock}')

class AddressForm(forms.Form):
    shipping_address_line_1 = forms.CharField(required=False)
    shipping_address_line_2 = forms.CharField(required=False)
    shipping_zip_code = forms.CharField(required=False)
    shipping_city = forms.CharField(required=False)

    billing_address_line_1 = forms.CharField(required=False)
    billing_address_line_2 = forms.CharField(required=False)
    billing_zip_code = forms.CharField(required=False)
    billing_city = forms.CharField(required=False)

    selected_shipping_address = forms.ModelChoiceField(
        Address.objects.none(),required=False
    )

    selected_billing_address = forms.ModelChoiceField(
        Address.objects.none(),required=False
    )

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        # if not user_id:            
        # raise forms.ValidationError(f'Debe iniciar sesión para terminar la compra') 
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
        self.fields['selected_billing_address'].queryset = billing_address_qs

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
        if selected_billing_address is None:
            if not data.get('billing_address_line_1', None):
                self.add_error('billing_address_line_1', "Por favor llene este campo")
            if not data.get('billing_address_line_2', None):
                self.add_error('billing_address_line_2', "Por favor llene este campo")
            if not data.get('billing_zip_code', None):
                self.add_error('billing_zip_code', "Por favor llene este campo")
            if not data.get('billing_city', None):
                self.add_error('billing_city', "Por favor llene este campo")
            
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
    # buyerFullName = forms.CharField(max_length=150)
    # shippingAddress = forms.CharField(max_length=255)
    # shippingCity = forms.CharField(max_length=50)
    # shippingCountry = forms.CharField(max_length=2)
    # telephone = forms.CharField(max_length=50)
    # ApiKey = forms.CharField()

    def __init__(self, *args, **kwargs):
        print('Diccionario contexto formm')
        user_id = kwargs.pop('user_id')
        order = kwargs.pop('order')
        super().__init__(*args, **kwargs)

        code_test = str(get_next_value("test_fake_2"))
        self.fields['merchantId'].initial = env('MERCHANID')
        self.fields['accountId'].initial = env('ACCOUNTID')
        self.fields['description'].initial = "Venta de prueba"
        self.fields['referenceCode'].initial = "TEST_RSS_0000" + code_test
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
        self.fields['test'].initial = 1
        self.fields['buyerEmail'].initial = 'luisgilsan_007@hotmail.com'
        self.fields['responseUrl'].initial = 'https://www.udemy.com/'
        self.fields['confirmationUrl'].initial = 'https://www.udemy.com/'
        print('En el formulario')

    def clean(self):
        # self.cleaned_data['shippingCity'] = 'AQUI'
        # self.cleaned_data['accountId'] =      
        # self.cleaned_data['merchantId'] =         
        

        
        
        print(self.cleaned_data)
        print('Ya estas vendiendo Chamo')