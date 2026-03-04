"""Seed data

Revision ID: 002_seed_data
Revises: 001_initial_schema
Create Date: 2024-01-01 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_seed_data"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert categories
    op.execute(
        """
        INSERT INTO categories (id, name, description) VALUES
        (1, 'Electronics', 'Electronic devices and accessories'),
        (2, 'Clothing', 'Apparel and fashion items'),
        (3, 'Home & Garden', 'Home improvement and garden supplies'),
        (4, 'Books', 'Physical and digital books'),
        (5, 'Sports & Outdoors', 'Sporting goods and outdoor equipment')
    """
    )

    # Insert products (50+ products to trigger N+1 issues)
    op.execute(
        """
        INSERT INTO products (sku, name, description, price, stock_quantity, category_id) VALUES
        -- Electronics (15 products)
        ('ELEC-001', 'Wireless Bluetooth Headphones', 'High-quality over-ear headphones with noise cancellation', 149.99, 50, 1),
        ('ELEC-002', 'USB-C Hub 7-in-1', 'Multi-port hub with HDMI, USB-A, and SD card reader', 49.99, 100, 1),
        ('ELEC-003', 'Mechanical Keyboard RGB', 'Gaming keyboard with Cherry MX switches', 129.99, 30, 1),
        ('ELEC-004', 'Wireless Mouse Ergonomic', 'Ergonomic vertical mouse with adjustable DPI', 39.99, 75, 1),
        ('ELEC-005', '4K Webcam Pro', 'Ultra HD webcam with auto-focus and mic', 89.99, 45, 1),
        ('ELEC-006', 'Portable SSD 1TB', 'Fast external solid state drive', 99.99, 60, 1),
        ('ELEC-007', 'Smart Watch Fitness', 'Fitness tracker with heart rate monitor', 199.99, 35, 1),
        ('ELEC-008', 'Wireless Earbuds Pro', 'True wireless earbuds with ANC', 179.99, 80, 1),
        ('ELEC-009', 'Monitor Stand Adjustable', 'Aluminum monitor arm with cable management', 79.99, 40, 1),
        ('ELEC-010', 'Power Bank 20000mAh', 'High capacity portable charger', 44.99, 120, 1),
        ('ELEC-011', 'Laptop Stand Aluminum', 'Foldable laptop riser for ergonomic setup', 34.99, 90, 1),
        ('ELEC-012', 'Smart Home Hub', 'Voice-controlled smart home controller', 129.99, 25, 1),
        ('ELEC-013', 'Wireless Charging Pad', 'Fast wireless charger for smartphones', 29.99, 150, 1),
        ('ELEC-014', 'Gaming Headset 7.1', 'Surround sound gaming headset', 79.99, 55, 1),
        ('ELEC-015', 'USB Microphone Studio', 'Condenser microphone for streaming', 109.99, 40, 1),

        -- Clothing (12 products)
        ('CLTH-001', 'Cotton T-Shirt Classic', 'Comfortable 100% cotton t-shirt', 24.99, 200, 2),
        ('CLTH-002', 'Denim Jeans Slim Fit', 'Modern slim fit denim jeans', 59.99, 150, 2),
        ('CLTH-003', 'Hoodie Pullover', 'Warm fleece pullover hoodie', 49.99, 100, 2),
        ('CLTH-004', 'Running Shoes Pro', 'Lightweight running shoes with cushioning', 89.99, 80, 2),
        ('CLTH-005', 'Winter Jacket Insulated', 'Water-resistant insulated jacket', 129.99, 45, 2),
        ('CLTH-006', 'Baseball Cap Adjustable', 'Classic adjustable baseball cap', 19.99, 300, 2),
        ('CLTH-007', 'Wool Sweater Crew', 'Merino wool crew neck sweater', 79.99, 60, 2),
        ('CLTH-008', 'Casual Shorts Khaki', 'Comfortable khaki shorts', 34.99, 120, 2),
        ('CLTH-009', 'Dress Shirt Oxford', 'Professional oxford dress shirt', 44.99, 90, 2),
        ('CLTH-010', 'Sneakers Canvas', 'Classic canvas sneakers', 54.99, 110, 2),
        ('CLTH-011', 'Beanie Knit Winter', 'Warm knit winter beanie', 14.99, 250, 2),
        ('CLTH-012', 'Athletic Socks 6-Pack', 'Performance athletic socks', 19.99, 400, 2),

        -- Home & Garden (10 products)
        ('HOME-001', 'Robot Vacuum Smart', 'Wi-Fi connected robot vacuum', 299.99, 30, 3),
        ('HOME-002', 'Air Purifier HEPA', 'Large room air purifier with HEPA filter', 179.99, 40, 3),
        ('HOME-003', 'Coffee Maker Programmable', '12-cup programmable coffee maker', 69.99, 55, 3),
        ('HOME-004', 'Standing Desk Electric', 'Height adjustable electric standing desk', 449.99, 20, 3),
        ('HOME-005', 'LED Desk Lamp Dimmable', 'Adjustable LED desk lamp with USB port', 39.99, 85, 3),
        ('HOME-006', 'Knife Set 15-Piece', 'Professional kitchen knife set with block', 149.99, 35, 3),
        ('HOME-007', 'Blender High-Speed', '1500W high-speed blender', 89.99, 50, 3),
        ('HOME-008', 'Garden Hose 100ft', 'Expandable garden hose with spray nozzle', 44.99, 70, 3),
        ('HOME-009', 'Outdoor Solar Lights 8-Pack', 'Solar powered pathway lights', 34.99, 100, 3),
        ('HOME-010', 'Throw Blanket Fleece', 'Soft fleece throw blanket', 29.99, 150, 3),

        -- Books (8 products)
        ('BOOK-001', 'Programming Python Advanced', 'Advanced Python programming techniques', 49.99, 60, 4),
        ('BOOK-002', 'Data Science Handbook', 'Comprehensive data science guide', 54.99, 45, 4),
        ('BOOK-003', 'Machine Learning Intro', 'Introduction to machine learning', 44.99, 70, 4),
        ('BOOK-004', 'System Design Interview', 'System design interview preparation', 39.99, 80, 4),
        ('BOOK-005', 'Clean Code Principles', 'Writing clean and maintainable code', 34.99, 90, 4),
        ('BOOK-006', 'Web Development Guide', 'Full-stack web development', 42.99, 55, 4),
        ('BOOK-007', 'DevOps Handbook', 'DevOps practices and principles', 47.99, 40, 4),
        ('BOOK-008', 'Algorithms Explained', 'Data structures and algorithms', 44.99, 65, 4),

        -- Sports & Outdoors (10 products)
        ('SPRT-001', 'Yoga Mat Premium', 'Non-slip exercise yoga mat', 34.99, 100, 5),
        ('SPRT-002', 'Dumbbell Set 50lb', 'Adjustable dumbbell set', 149.99, 30, 5),
        ('SPRT-003', 'Resistance Bands Set', '5-piece resistance bands with handles', 24.99, 150, 5),
        ('SPRT-004', 'Camping Tent 4-Person', 'Waterproof 4-person camping tent', 189.99, 25, 5),
        ('SPRT-005', 'Hiking Backpack 50L', 'Large hiking backpack with rain cover', 79.99, 45, 5),
        ('SPRT-006', 'Bike Helmet Adult', 'Lightweight adult bike helmet', 49.99, 70, 5),
        ('SPRT-007', 'Sleeping Bag 20F', 'Cold weather sleeping bag', 89.99, 35, 5),
        ('SPRT-008', 'Jump Rope Speed', 'Adjustable speed jump rope', 14.99, 200, 5),
        ('SPRT-009', 'Foam Roller Recovery', 'High-density foam roller', 29.99, 80, 5),
        ('SPRT-010', 'Water Bottle Insulated', '32oz insulated water bottle', 24.99, 180, 5)
    """
    )

    # Reset sequence to continue from the last inserted ID
    op.execute("SELECT setval('categories_id_seq', 5)")
    op.execute("SELECT setval('products_id_seq', 55)")


def downgrade() -> None:
    op.execute("DELETE FROM products")
    op.execute("DELETE FROM categories")
