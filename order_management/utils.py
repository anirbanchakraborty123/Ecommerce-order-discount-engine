from decimal import Decimal
from django.core.cache import cache
from django.db import transaction
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
class DiscountCalculator:
    """Handles discount calculations for orders"""

    def __init__(self, order):
        self.order = order
        self.discount_breakdown = {}
        self.applied_discounts = []

    def calculate_discounts(self):
        """Calculate all applicable discounts"""
        # Reset discount amounts
        self.order.total_discount = Decimal("0")
        self.discount_breakdown = {}

        # Apply discounts in priority order
        self._apply_percentage_discount()
        self._apply_flat_discount()
        self._apply_category_discounts()

        # Update order with discount breakdown
        self.order.discount_breakdown = self.discount_breakdown
        self.order.save()

        return self.order.total_discount

    def _apply_percentage_discount(self):
        """Apply percentage discount if order meets criteria"""
        from .models import DiscountRule

        percentage_rules = [
            rule
            for rule in DiscountRule.get_active_rules()
            if rule.discount_type == "percentage"
            and (
                rule.min_order_amount is None
                or self.order.subtotal >= rule.min_order_amount
            )
        ]

        if not percentage_rules:
            return

        # Get the highest priority percentage rule
        rule = percentage_rules[0]
        discount_amount = (self.order.subtotal * rule.value) / Decimal("100")

        # Check if this is better than any existing percentage discount
        existing_percentage = self.discount_breakdown.get(
            "percentage_discount", {}
        ).get("amount", Decimal("0"))
        if discount_amount > existing_percentage:
            self.order.total_discount += discount_amount - existing_percentage
            self.discount_breakdown["percentage_discount"] = {
                "type": "percentage",
                "name": rule.name,
                "value": float(rule.value),
                "amount": float(discount_amount),
                "rule_id": rule.id,
            }

    def _apply_flat_discount(self):
        """Apply flat discount if user is eligible"""
        from .models import DiscountRule

        flat_rules = [
            rule
            for rule in DiscountRule.get_active_rules()
            if rule.discount_type == "flat"
            and (
                rule.min_completed_orders is None
                or self.order.user.eligible_for_flat_discount
            )
        ]

        if not flat_rules:
            return

        # Get the highest priority flat rule
        rule = flat_rules[0]
        discount_amount = rule.value

        # Only apply if it's better than existing flat discount
        existing_flat = self.discount_breakdown.get("flat_discount", {}).get(
            "amount", Decimal("0")
        )

        if discount_amount > existing_flat:
            self.order.total_discount += discount_amount - existing_flat

            self.discount_breakdown["flat_discount"] = {
                "type": "flat",
                "name": rule.name,
                "value": float(rule.value),
                "amount": float(discount_amount),
                "rule_id": rule.id,
            }

    def _apply_category_discounts(self):
        """Apply category-specific discounts"""
        from .models import DiscountRule

        # Get all active category-based discount rules
        category_rules = [
            rule
            for rule in DiscountRule.get_active_rules()
            if rule.discount_type == "category" and rule.category is not None
        ]
        if not category_rules:
            return
        # Group order items by category
        category_items = {}
        for item in self.order.items.all():
            if item.category_id not in category_items:
                category_items[item.category_id] = []
            category_items[item.category_id].append(item)

        # Apply category discounts
        for rule in category_rules:
            if rule.category_id in category_items:
                items = category_items[rule.category_id]
                total_quantity = sum(item.quantity for item in items)
                if rule.min_quantity is None or total_quantity >= rule.min_quantity:
                    # Apply discount to each item in category
                    for item in items:
                        discount_per_item = (item.unit_price * rule.value) / Decimal(
                            "100"
                        )
                        total_discount = discount_per_item * item.quantity

                        item.item_discount = total_discount
                        item.save()

                        self.order.total_discount += total_discount

                    # Record in breakdown
                    category_key = f"category_discount_{rule.category_id}"
                    self.discount_breakdown[category_key] = {
                        "type": "category",
                        "name": rule.name,
                        "category": rule.category.name,
                        "value": float(rule.value),
                        "amount": float(sum(item.item_discount for item in items)),
                        "rule_id": rule.id,
                    }
