from rest_framework import serializers
from .models import Product, Order, OrderItem, DiscountRule


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model """
    
    category = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 
            'category', 'stock_quantity', 'is_active'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """ Serializer for OrderItem model"""
    product = ProductSerializer()
    category = serializers.StringRelatedField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'unit_price',
            'category', 'item_discount'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """ Serializer for Order model"""
    
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'order_date', 'status',
            'subtotal', 'total_discount', 'final_amount',
            'is_cancelled', 'is_returned', 'discount_breakdown','items'
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """ Serializer for creating order items """
    
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """ Serializer for creating orders"""
    
    items = OrderItemCreateSerializer(many=True, min_length=1)
    
    def validate(self, data):
        """Validate order data"""
        # Check product availability
        for item in data['items']:
            product = item['product_id']
            if product.stock_quantity < item['quantity']:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}"
                )
        return data


class DiscountRuleSerializer(serializers.ModelSerializer):
    """ Serializer for DiscountRule model """
    category = serializers.StringRelatedField()
    
    class Meta:
        model = DiscountRule
        fields = [
            'id', 'name', 'discount_type', 'value',
            'min_order_amount', 'min_quantity', 'category',
            'min_completed_orders', 'is_active', 'priority'
        ]