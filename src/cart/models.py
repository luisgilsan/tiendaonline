from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.shortcuts import reverse
from django.core.validators import MaxValueValidator
from datetime import datetime
from sequences import get_next_value

User = get_user_model()

TRANSACTIONSTATECHOISES = (	
    (4,'Aprobada'), 
    (6,'Declinada'),
    (104,'Error'), 
    (5,'Expirada'),
    (7,'Pendiente'),
    (None,'Desconocido')
)
POLTRANSACTIONSTATE = (
    (4, 'Aprobada'),
    (6, 'Rechazada'),
    (5, 'Expirada'),
    (14, 'Pendiente'),
    (7, 'Pendiente'),
    (15, 'Pendiente'),
    (10, 'Pendiente'),
    (12, 'Pendiente'),
    (18, 'Pendiente'),
    (None,'Desconocido')
)
POLPAYMENTMETHODTYPE = (
    (2,	'CREDIT_CARD'),
    (4,	'PSE'),
    (5,	'ACH'),
    (6,	'DEBIT_CARD'),
    (7,	'CASH'),
    (8,	'REFERENCED'),
    (10, 'BANK_REFERENCED'),
    (14, 'SPEI'),
    (None,'Desconocido')
)
POLPAYMENRESPONSE = (
    ('confirm',	'Confirmado'),
    ('response', 'Respuesta'),
    (None,'Desconocido')
)
ORDER_STATES = (
    ('draft','Borrador'),
    ('pending','Pendiente'),
    ('paid','Pagado'),
)

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

class DataSheet(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ficha Técnica'
        verbose_name_plural = 'Fichas tecnicas'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

class Address(models.Model):
    ADDRESS_CHOICES = (
        ('B','Billing'),
        ('S','Shipping'),
    )
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1,choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}"
    
    class Meta:
        verbose_name_plural = 'Direcciones'

class ColourVariation(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return   self.name

class SizeVariation(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return   self.name
        
class Product(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='product_images')
    descripcion = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=False)
    available_colours = models.ManyToManyField(ColourVariation)
    available_sizes = models.ManyToManyField(SizeVariation)
    price = models.IntegerField(default=0)
    primary_category_id = models.ForeignKey(Category, related_name='primary_products', on_delete=models.CASCADE,blank=True,null=True)
    secondary_categories = models.ManyToManyField(Category, blank=True)
    stock = models.IntegerField(verbose_name="Cantidad",default=0)
    datasheet_id = models.ManyToManyField(DataSheet, related_name='product_ids',blank=True,verbose_name="Atributos")
    brand_id = models.ForeignKey(Brand, related_name='product_ids',blank=True,null=True, verbose_name="Marca", on_delete=models.SET_NULL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cart:product_detail", kwargs={'slug': self.slug})

    def get_price(self):
        return "{:-2f}".format(self.price/100)

    def _discount_qty(self,qty):
        self.stock -= qty
        self.save()
    
    @property
    def in_stock(self):
        return self.stock > 0

class OrderItem(models.Model):
    order = models.ForeignKey("Order",related_name='items',on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    colour = models.ForeignKey(ColourVariation,on_delete=models.CASCADE,blank=True,null=True)
    size = models.ForeignKey(SizeVariation,on_delete=models.CASCADE,blank=True,null=True)

    class Meta():
        ordering = ['pk']

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_raw_total_item_price(self):
        return self.quantity*self.product.price

    def get_total_item_price(self):
        price =  self.get_raw_total_item_price()
        return "{:-2f}".format(price/100)
    
class Order(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    name = models.CharField(max_length=255,blank=True,null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(blank=True,null=True)
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(Address, related_name='billing_address', blank=True, null=True,
        on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(Address, related_name='shipping_address', blank=True, null=True,
        on_delete=models.SET_NULL)
    sended_signature = models.CharField(max_length=255,blank=True,null=True )
    sender_reference = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)
    payu_payment_id = models.ForeignKey("PayuPayment",related_name='order_id',on_delete=models.SET_NULL,
        blank=True,null=True)
    state = models.CharField(max_length=20, choices=ORDER_STATES, default='draft')
    

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"ORDEN-00{self.pk}"

    def get_raw_subtotal(self):
        total = 0
        total = sum([order_item.get_raw_total_item_price() for order_item in self.items.all()])
        return total

    def get_subtotal(self):
        subtotal = self.get_raw_subtotal()
        return "{:.2f}".format(subtotal/100)

    def get_raw_total(self):
        subtotal = self.get_raw_subtotal()
        # Agregar costo envio, impuestos, restar descuentos
        return subtotal

    def get_total(self):
        total = self.get_raw_total()
        return "{:.2f}".format(total/100)

    def pay(self):
        self.state = 'paid'
        self.inventory_discount()
        self.save()

    def inventory_discount(self):
        for item in self.items.all():
            item.product._discount_qty(item.quantity)
            
class PayuPayment(models.Model):

    name = models.CharField(max_length=255,blank=True,null=True,default='PAYU-PAYMENT-00' + str(get_next_value("payment_secuence")))
    transaction_state = models.PositiveIntegerField(choices=TRANSACTIONSTATECHOISES,
        validators=[MaxValueValidator(9999)],blank=True,null=True)
    pol_response_code = models.PositiveIntegerField(validators=[MaxValueValidator(999999)],default=0)
    pol_payment_method_type = models.PositiveIntegerField(choices=POLPAYMENTMETHODTYPE,
        blank=True,null=True)
    lap_response_code = models.CharField(max_length=100,blank=True,null=True)
    lap_transaction_state = models.CharField(max_length=100,blank=True,null=True)
    value = models.FloatField(default=0)
    reponse_method = models.CharField(max_length=25,choices=POLPAYMENRESPONSE,default='confirm',blank=True,null=True)
    response_message_pol = models.CharField(max_length=100,default=None,blank=True,null=True)
    payment_method_id  = models.PositiveIntegerField(choices=TRANSACTIONSTATECHOISES,
        validators=[MaxValueValidator(9999)])
    lap_payment_method_type = models.CharField(max_length=100,default=None,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(('paypal','Paypal'),))
    timestamp = models.DateTimeField(auto_now_add=True)
    sucessful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
         return f"PAGO-{self.order}-00{self.pk}"

def pre_save_product_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)

pre_save.connect(pre_save_product_receiver, sender=Product)