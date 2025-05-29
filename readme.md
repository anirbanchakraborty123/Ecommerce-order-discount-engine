# E-Commerce Discount Engine

**Technologies Used**: Python, Django, Django REST Framework (DRF)

A robust discount engine for e-commerce platforms with dynamic rule application and product recommendations.

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Products](#products)
  - [Orders](#orders)
  - [Discounts (Admin Only)](#discounts-admin-only)
- [Admin Panel](#admin-panel)

## Features
1. **Multiple Discount Types**:
   - Percentage discounts based on order value
   - Flat discounts for loyal customers
   - Category-based discounts for specific product categories

2. **Stackable Discounts**:
   - Multiple discounts can apply to an order
   - Priority-based application of discounts
   - Ensures maximum customer benefit

3. **Admin Configuration**:
   - Dynamic discount rule management
   - Real-time updates to discount logic

4. **Performance Optimizations**:
   - Caching for frequently accessed discount rules
   - Efficient discount calculation algorithms
   - Added pagination for large datasets

5. **Authentication**:
   - Added JWT authentication for security and access control. 

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (recommended) or SQLite
- pip package manager

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/anirbanchakraborty123/Ecommerce-order-discount-engine.git
    cd ecommerce
    ```

2. Create and activate virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate    # Windows
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Configure database in `ecommerce/settings.py , if needed`:

    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'ecommerce',
            'USER': 'youruser',
            'PASSWORD': 'yourpassword',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    ```

5. Run migrations:

    ```bash
    python manage.py migrate
    ```

6. Create superuser:

    ```bash
    python manage.py createsuperuser
    ```

7. Run development server:

    ```bash
    python manage.py runserver
    ```

## API Documentation

**Base URL:** `http://localhost:8000/api/`

### Authentication

#### Obtain Token

**Request:**

```http
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "refresh": "xxxxx",
  "access": "xxxxx"
}
```

#### Refresh Token

**Request:**

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "your_refresh_token"
}
```

**Response:**

```json
{
  "access": "new_access_token"
}
```

### Products

#### List Products

**Request:**

```http
GET /api/products/?category=Electronics&page=2
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/products/?category=Electronics&page=3",
  "previous": "http://localhost:8000/api/products/?category=Electronics",
  "results": [
    {
      "id": 1,
      "name": "Smartphone",
      "description": "Latest model smartphone",
      "price": "999.99",
      "category": "Electronics",
      "stock_quantity": 50,
      "is_active": true
    }
  ]
}
```

### Orders

#### Create Order

**Request:**

```http
POST /api/orders/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 3,
      "quantity": 1
    }
  ]
}
```

**Response:**

```json
{
  "id": 123,
  "user": "username",
  "order_date": "2023-01-01T12:00:00Z",
  "status": "pending",
  "subtotal": "2999.97",
  "total_discount": "299.99",
  "final_amount": "2699.98",
  "discount_breakdown": {
    "percentage_discount": {
      "type": "percentage",
      "name": "10% off on orders over ₹5000",
      "value": 10.0,
      "amount": 299.99,
      "rule_id": 1
    }
  },
  "items": [
    {
      "id": 456,
      "product": {
        "id": 1,
        "name": "Smartphone"
      },
      "quantity": 2,
      "unit_price": "999.99",
      "category": "Electronics",
      "item_discount": "0.00"
    }
  ]
}
```

#### List Orders

**Request:**

```http
GET /api/orders/
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 123,
      "user": "username",
      "order_date": "2023-01-01T12:00:00Z",
      "status": "completed",
      "final_amount": "2699.98"
    }
  ]
}
```

### Discounts (Admin Only)

#### List Discount Rules

**Request:**

```http
GET /api/discount-rules/
Authorization: Bearer <admin_access_token>
```

**Response:**

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "10% off on orders over ₹5000",
      "discount_type": "percentage",
      "value": "10.00",
      "min_order_amount": "5000.00",
      "is_active": true
    }
  ]
}
```

## Admin Panel

Access the admin interface at `http://localhost:8000/admin/` to:

- Manage products and categories
- View and update orders
- Configure discount rules
- Manage users

<p align="center">Made with ❤️ by <strong>ANIRBAN.C</strong></p>