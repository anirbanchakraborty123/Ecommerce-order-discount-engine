from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProductListView,
    OrderListView,
    OrderDetailView,
    DiscountRuleListView,
    DiscountRuleDetailView
)

router = DefaultRouter()

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('discount-rules/', DiscountRuleListView.as_view(), name='discount-rule-list'),
    path('discount-rules/<int:pk>/', DiscountRuleDetailView.as_view(), 
         name='discount-rule-detail'),
] + router.urls