from django.contrib import admin
from .models import (
    Product,
    Order,
    OrderItem,
    ColourVariation,
    SizeVariation,
    Address,
    PayuPayment,
    Payment,
    Category,
    DataSheet,
    Brand,
    ProductImage
    )

class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'address_line_1',
        'address_line_2',
        'zip_code',
        'city',
        'address_type'
    ]   

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class DataSheetInline(admin.TabularInline):
    model = DataSheet
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline,DataSheetInline]
    list_display = [        
        'title',
        'descripcion',
        'price',
    ]
    search_fields = ['title']
    readonly_fields = ['created', 'update']

class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at',)

class DataSheetAdmin(admin.ModelAdmin):
    search_fields = ['product_id__title']

admin.site.register(Product,ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(ColourVariation)
admin.site.register(SizeVariation)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment)
admin.site.register(PayuPayment)
admin.site.register(Category)
admin.site.register(DataSheet,DataSheetAdmin)
admin.site.register(Brand)