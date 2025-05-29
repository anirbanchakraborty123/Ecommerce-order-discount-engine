from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db import transaction

from .models import Product, Order, OrderItem, DiscountRule
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    DiscountRuleSerializer
)
from .utils import DiscountCalculator

class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductListView(generics.ListAPIView):
    """List all available products with pagination """
    
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Optionally filter by category """
        
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        
        if category:
            queryset = queryset.filter(category__name__iexact=category)
        return queryset.order_by('name')

class OrderListView(generics.ListCreateAPIView):
    """ List and create orders for the authenticated users """
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """ Only show orders for the current user """
        return Order.objects.filter(user=self.request.user).order_by('-order_date')
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new order with items and apply discounts """
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=0,  # Will be calculated when items are added
            status='pending'
        )
        
        # Create order items
        items_data = serializer.validated_data['items']
        for item_data in items_data:
            product = item_data['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price,
                category=product.category
            )
        
        # Calculate discounts
        DiscountCalculator(order).calculate_discounts()
        
        # Return created order
        headers = self.get_success_headers(serializer.data)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve order details"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only allow viewing own orders"""
        return Order.objects.filter(user=self.request.user)


class DiscountRuleListView(generics.ListAPIView):
    """List all active discount rules (admin only)"""
    queryset = DiscountRule.objects.filter(is_active=True)
    serializer_class = DiscountRuleSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination


class DiscountRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ Manage discount rules (for admins only) """
    queryset = DiscountRule.objects.all()
    serializer_class = DiscountRuleSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_update(self, serializer):
        """Clear discount rules cache on update """
        
        super().perform_update(serializer)
        cache.delete('active_discount_rules')
    
    def perform_destroy(self, instance):
        """Clear discount rules cache on delete"""
        super().perform_destroy(instance)
        cache.delete('active_discount_rules')