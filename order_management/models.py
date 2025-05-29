from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Sum, F, Count
from django.conf import settings
from .utils import DiscountCalculator
class CustomUser(AbstractUser):
    """Extended user model for e-commerce platform"""
    loyalty_points = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    @property
    def eligible_for_flat_discount(self):
        """Check if user is eligible for flat discount based on purchase history"""
        cache_key = f'user_{self.id}_flat_discount_eligible'
        eligible = cache.get(cache_key)
        
        if eligible is None:
            # Count completed orders (excluding cancelled/returned)
            completed_orders = self.orders.filter(
                status='completed',
                is_cancelled=False,
                is_returned=False
            ).count()
            
            eligible = completed_orders >= 5
            cache.set(cache_key, eligible, timeout=3600)  # Cache for 1 hour
        
        return eligible
    
    def update_loyalty_points(self):
        """Update user's loyalty points based on purchase history"""
        total_spent = self.orders.filter(
            status='completed',
            is_cancelled=False,
            is_returned=False
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        # 1 point for every ₹100 spent -- added extra requirements
        self.loyalty_points = total_spent//100
        self.save()


class ProductCategory(models.Model):
    """Product category model"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Default discount percentage for this category"
    )
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.PROTECT,
        related_name='products'
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (₹{self.price})"


class DiscountRule(models.Model):
    """Model for configurable discount rules"""
    
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('flat', 'Flat Discount'),
        ('category', 'Category-Based Discount'),
    )
    
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum order amount for discount to apply"
    )
    min_quantity = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Minimum quantity for category-based discounts"
    )
    category = models.ForeignKey(
        ProductCategory, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        help_text="applicable category for category-based discounts"
    )
    min_completed_orders = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum completed orders for flat discount eligibility"
    )
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(
        default=0,
        help_text="higher priority discounts are applied first"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"
    
    @classmethod
    def get_active_rules(cls):
        """Get cached active discount rules"""
        cache_key = 'active_discount_rules'
        rules = cache.get(cache_key)
        
        if rules is None:
            rules = list(cls.objects.filter(is_active=True).order_by('-priority'))
            cache.set(cache_key, rules, timeout=300)  # Cache for 5 minutes
        
        return rules


class Order(models.Model):
    """Order model"""
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    )
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT,
        related_name='orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS, 
        default='pending'
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_cancelled = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    discount_breakdown = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
        def calculate_discounts(self):
        """Calculate all applicable discounts for this order"""
        calculator = DiscountCalculator(self)
        return calculator.calculate_discounts()
    
    def save(self, *args, **kwargs):
        """Override save to ensure proper amounts are set"""
        
        if not self.pk:
            # New order - calculate subtotal from items
            super().save(*args, **kwargs)
            return
        
        # Calculate final amount
        self.final_amount = self.subtotal - self.total_discount
        super().save(*args, **kwargs)
        
        # Update user's loyalty points if order is completed
        if self.status == 'completed' and not self.is_cancelled and not self.is_returned:
            self.user.update_loyalty_points()

class OrderItem(models.Model):
    """Items within an order"""
    
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='items'
        )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT,
        related_name='order_items'
     )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.PROTECT
    )
    
    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ('order', 'product')
    
    def __str__(self):
        return f" {self.quantity} x {self.product.name}--(Order #{self.order.id}) "
    
    def save(self, *args, **kwargs):
        """Set unit price and category from product if not set """
        
        if not self.unit_price:
            self.unit_price = self.product.price
        if not self.category_id:
            self.category = self.product.category
        
        super().save(*args, **kwargs)
        
        # Update order subtotal when item is saved
        if self.order_id:
            self.order.subtotal = self.order.items.aggregate(
                total=Sum(F('quantity') * F('unit_price')))['total'] or 0
            self.order.save()