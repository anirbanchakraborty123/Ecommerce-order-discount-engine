from django.contrib import admin
from django.db.models import Count, Sum
from django.core.cache import cache
from .models import (
    CustomUser, ProductCategory, Product,
    Order, OrderItem, DiscountRule
)

class OrderItemInline(admin.TabularInline):
    """ Inline admin for OrderItems """
    
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price', 'category', 'item_discount']
    fields = ['product', 'quantity', 'unit_price', 'category', 'item_discount']


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    """ Admin configuration for User model """
    list_display = ['username', 'email', 'loyalty_points']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    readonly_fields = ['loyalty_points']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ProductCategory"""
    list_display = ['name', 'discount_percentage']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product"""
    
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['price', 'stock_quantity', 'is_active']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """ Admin configuration for Order"""
    
    list_display = [
        'id', 'user', 'order_date', 'status',
        'subtotal', 'total_discount', 'final_amount'
    ]
    list_filter = ['status', 'is_cancelled', 'is_returned']
    
    search_fields = ['user__username', 'id']
    
    readonly_fields = [
        'subtotal', 'total_discount', 'final_amount',
        'discount_breakdown'
    ]
    inlines = [OrderItemInline]
    
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark orders as completed"""
        
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected orders as completed"


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    """Admin configuration for DiscountRule """
    
    list_display = [
        'name', 'discount_type', 'value', 'is_active',
        'priority', 'min_order_amount', 'min_quantity',
        'category', 'min_completed_orders'
    ]
    list_filter = ['discount_type', 'is_active']
    
    search_fields = ['name']
    
    list_editable = ['is_active', 'priority', 'value']
    
    def save_model(self, request, obj, form, change):
        """Clear discount rules cache on save """
        
        super().save_model(request, obj, form, change)
        cache.delete('active_discount_rules')