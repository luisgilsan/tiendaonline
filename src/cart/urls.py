from django.urls import path
from . import views
app_name = 'cart'

urlpatterns = [
    path('',views.CartView.as_view(), name='summary'),
    path('shop/',views.ProductListView.as_view(),name='product_list'),
    path('shop/<slug>/',views.ProductDetailView.as_view(),name='product_detail'),
    path('increase-quantity/<pk>/', views.IncreaseQuantityView.as_view(),name='increase_quantity'),
    path('diminish-quantity/<pk>/', views.DiminishQuantityView.as_view(),name='diminish_quantity'),
    path('delte-order_item/<pk>/', views.DeleteOrderItemView.as_view(),name='delete_order_item'),
    path('checkout/', views.CheckoutView.as_view(),name='checkout'),
    path('payment/', views.PaymentView.as_view(),name='payment'),
    path('thanks/', views.ThankYouView.as_view(),name='thanks-you'),
    path('confirm-order/', views.ConfirmOrderView.as_view(),name='confirm-order'),
    path('orders/<pk>/', views.OrderDetailView.as_view(),name='order-detail'),
]