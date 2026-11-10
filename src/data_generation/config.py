"""
Synthetic Data Generation Configuration.
Defines scale benchmarks, random seeds, and categorical lookup taxonomies.
"""

from dataclasses import dataclass

RANDOM_SEED: int = 20261022

@dataclass(frozen=True)
class ScaleConfig:
    customers: int
    products: int
    orders: int
    engagement_events: int
    support_cases: int

SCALE_PROFILES: dict[str, ScaleConfig] = {
    "starter": ScaleConfig(
        customers=100,
        products=40,
        orders=400,
        engagement_events=2000,
        support_cases=60
    ),
    "medium": ScaleConfig(
        customers=5000,
        products=150,
        orders=20000,
        engagement_events=100000,
        support_cases=3000
    ),
    "full": ScaleConfig(
        customers=50000,
        products=500,
        orders=200000,
        engagement_events=1000000,
        support_cases=30000
    ),
}

# Master Taxonomies
ACQUISITION_CHANNELS = ["Organic", "Paid Search", "Social Media", "Email Referral", "Direct"]
LIFECYCLE_STAGES = ["Prospect", "Active", "Dormant", "Churned"]
ORDER_CHANNELS = ["Web", "Mobile App", "In-Store", "Affiliate"]
ORDER_STATUSES = ["Delivered", "Shipped", "Processing", "Cancelled", "Returned"]
EVENT_TYPES = ["page_view", "product_view", "add_to_cart", "email_open", "email_click", "app_login", "search"]
EVENT_CHANNELS = ["Web", "Mobile App", "Email", "SMS", "Push"]
DEVICE_TYPES = ["Desktop", "Mobile", "Tablet", "Other"]
CASE_CATEGORIES = ["Billing", "Shipping", "Product Defect", "Return Request", "General Inquiry"]
CASE_PRIORITIES = ["Low", "Medium", "High", "Critical"]
CASE_STATUSES = ["Resolved", "Closed", "In Progress", "Open"]
CONSENT_CHANNELS = ["Email", "SMS", "Push Notification"]
CONSENT_TYPES = ["Marketing", "Transactional", "Analytics"]

PRODUCT_CATEGORIES: dict[str, list[tuple[str, float, float]]] = {
    "Electronics": [
        ("Noise-Cancelling Headphones", 149.99, 65.00),
        ("Wireless Mechanical Keyboard", 89.99, 40.00),
        ("Ultra-HD Webcam 4K", 119.50, 52.00),
        ("Bluetooth Smart Speaker", 49.99, 21.00),
        ("Multi-Port USB-C Hub", 34.99, 12.50),
        ("Gaming Optical Mouse", 59.99, 24.00),
        ("Fast Wireless Charger Pad", 25.00, 9.00),
        ("Portable Power Bank 20000mAh", 39.99, 16.00)
    ],
    "Apparel": [
        ("Classic Cotton Crewneck T-Shirt", 24.50, 7.50),
        ("Slim-Fit Stretch Denim Jeans", 68.00, 22.00),
        ("Waterproof Windbreaker Jacket", 95.00, 34.00),
        ("Merino Wool Knit Sweater", 85.00, 31.00),
        ("Breathable Athletic Shorts", 32.00, 10.00),
        ("Everyday Casual Canvas Sneakers", 55.00, 18.00)
    ],
    "Home & Kitchen": [
        ("Stainless Steel Chef Knife 8-inch", 45.00, 15.00),
        ("Pour-Over Glass Coffee Maker", 29.99, 9.50),
        ("Cast Iron Skillet Pre-Seasoned", 38.50, 14.00),
        ("Scented Aromatherapy Diffuser", 22.00, 6.80),
        ("Organic Bamboo Cutting Board Set", 27.50, 8.20),
        ("Silicone Cooking Utensil 10pc Set", 19.99, 6.00)
    ],
    "Beauty": [
        ("Hydrating Hyaluronic Acid Serum", 26.00, 5.50),
        ("Gentle Foaming Daily Cleanser", 18.50, 4.20),
        ("Broad Spectrum SPF 50 Mineral Sunscreen", 22.00, 5.00),
        ("Nourishing Vitamin E Night Cream", 34.00, 8.00),
        ("Purifying Clay Face Mask", 16.00, 3.50)
    ],
    "Sports": [
        ("High-Density Anti-Tear Yoga Mat", 28.00, 9.00),
        ("Adjustable Dumbbell Pair 25lb", 120.00, 55.00),
        ("Insulated Stainless Water Bottle 32oz", 24.99, 7.00),
        ("Elastic Resistance Bands 5-Pack", 15.00, 3.80),
        ("Compact Foam Roller for Muscle Recovery", 19.99, 5.50)
    ]
}

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Arun", "Priya", "Rahul", "Ananya", "Ravi", "Sneha", "Karthik", "Divya", "Suresh", "Pooja"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Sharma", "Patel", "Verma", "Rao", "Iyer", "Reddy", "Nair", "Kulkarni", "Gupta"
]

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "proton.me", "example.com"]
