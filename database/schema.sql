PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS action_outcomes;
DROP TABLE IF EXISTS action_catalogs;
DROP TABLE IF EXISTS segment_memberships;
DROP TABLE IF EXISTS segment_rules;
DROP TABLE IF EXISTS consents;
DROP TABLE IF EXISTS support_cases;
DROP TABLE IF EXISTS engagement_events;
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id          TEXT PRIMARY KEY,
    first_name           TEXT NOT NULL,
    last_name            TEXT NOT NULL,
    email                TEXT NOT NULL UNIQUE,
    phone                TEXT,
    acquisition_channel  TEXT NOT NULL CHECK(acquisition_channel IN ('Organic', 'Paid Search', 'Social Media', 'Email Referral', 'Direct')),
    lifecycle_stage      TEXT NOT NULL CHECK(lifecycle_stage IN ('Prospect', 'Active', 'Dormant', 'Churned')),
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);

CREATE TABLE products (
    product_id           TEXT PRIMARY KEY,
    product_name         TEXT NOT NULL,
    category             TEXT NOT NULL CHECK(category IN ('Electronics', 'Apparel', 'Home & Kitchen', 'Beauty', 'Sports')),
    base_price           REAL NOT NULL CHECK(base_price >= 0.0),
    cost                 REAL NOT NULL CHECK(cost >= 0.0),
    is_active            INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at           TEXT NOT NULL
);

CREATE TABLE orders (
    order_id             TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date           TEXT NOT NULL,
    order_status         TEXT NOT NULL CHECK(order_status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned')),
    channel              TEXT NOT NULL CHECK(channel IN ('Web', 'Mobile App', 'In-Store', 'Affiliate')),
    subtotal_amount      REAL NOT NULL CHECK(subtotal_amount >= 0.0),
    discount_amount      REAL NOT NULL DEFAULT 0.0 CHECK(discount_amount >= 0.0),
    tax_amount           REAL NOT NULL DEFAULT 0.0 CHECK(tax_amount >= 0.0),
    total_amount         REAL NOT NULL CHECK(total_amount >= 0.0),
    net_amount           REAL NOT NULL,
    created_at           TEXT NOT NULL
);

CREATE TABLE order_lines (
    order_line_id        TEXT PRIMARY KEY,
    order_id             TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id           TEXT NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity             INTEGER NOT NULL CHECK(quantity > 0),
    unit_price           REAL NOT NULL CHECK(unit_price >= 0.0),
    line_total           REAL NOT NULL CHECK(line_total >= 0.0),
    is_returned          INTEGER NOT NULL DEFAULT 0 CHECK(is_returned IN (0, 1)),
    return_amount        REAL NOT NULL DEFAULT 0.0 CHECK(return_amount >= 0.0),
    return_date          TEXT,
    created_at           TEXT NOT NULL
);

CREATE TABLE engagement_events (
    event_id             TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    event_type           TEXT NOT NULL CHECK(event_type IN ('page_view', 'product_view', 'add_to_cart', 'email_open', 'email_click', 'app_login', 'search')),
    channel              TEXT NOT NULL CHECK(channel IN ('Web', 'Mobile App', 'Email', 'SMS', 'Push')),
    event_timestamp      TEXT NOT NULL,
    session_id           TEXT NOT NULL,
    device_type          TEXT NOT NULL CHECK(device_type IN ('Desktop', 'Mobile', 'Tablet', 'Other')),
    page_url             TEXT
);

CREATE TABLE support_cases (
    case_id              TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_id             TEXT REFERENCES orders(order_id) ON DELETE SET NULL,
    case_category        TEXT NOT NULL CHECK(case_category IN ('Billing', 'Shipping', 'Product Defect', 'Return Request', 'General Inquiry')),
    priority             TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
    status               TEXT NOT NULL CHECK(status IN ('Open', 'In Progress', 'Resolved', 'Closed')),
    cost_amount          REAL NOT NULL DEFAULT 0.0 CHECK(cost_amount >= 0.0),
    resolution_notes     TEXT,
    opened_at            TEXT NOT NULL,
    closed_at            TEXT
);

CREATE TABLE consents (
    consent_id           TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    channel              TEXT NOT NULL CHECK(channel IN ('Email', 'SMS', 'Push Notification', 'Phone Call', 'Direct Mail')),
    consent_type         TEXT NOT NULL CHECK(consent_type IN ('Marketing', 'Transactional', 'Data Processing', 'Analytics')),
    status               TEXT NOT NULL CHECK(status IN ('Opted In', 'Opted Out', 'Pending')),
    effective_from       TEXT NOT NULL,
    effective_to         TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    version              INTEGER NOT NULL DEFAULT 1 CHECK(version > 0),
    updated_at           TEXT NOT NULL
);

CREATE TABLE segment_rules (
    segment_id           TEXT PRIMARY KEY,
    segment_name         TEXT NOT NULL UNIQUE,
    rfm_cell             TEXT,
    min_recency_days     INTEGER CHECK(min_recency_days IS NULL OR min_recency_days >= 0),
    max_recency_days     INTEGER CHECK(max_recency_days IS NULL OR max_recency_days >= 0),
    min_frequency        INTEGER CHECK(min_frequency IS NULL OR min_frequency >= 0),
    max_frequency        INTEGER CHECK(max_frequency IS NULL OR max_frequency >= 0),
    min_monetary         REAL CHECK(min_monetary IS NULL OR min_monetary >= 0.0),
    max_monetary         REAL CHECK(max_monetary IS NULL OR max_monetary >= 0.0),
    is_exclusive         INTEGER NOT NULL DEFAULT 1 CHECK(is_exclusive IN (0, 1)),
    priority_order       INTEGER NOT NULL DEFAULT 1 CHECK(priority_order > 0),
    description          TEXT NOT NULL,
    is_active            INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at           TEXT NOT NULL
);

CREATE TABLE segment_memberships (
    membership_id        TEXT PRIMARY KEY,
    segment_id           TEXT NOT NULL REFERENCES segment_rules(segment_id) ON DELETE RESTRICT,
    customer_id          TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    assigned_date        TEXT NOT NULL,
    valid_from           TEXT NOT NULL,
    valid_to             TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    confidence_score     REAL NOT NULL DEFAULT 1.0 CHECK(confidence_score BETWEEN 0.0 AND 1.0),
    assignment_reason    TEXT NOT NULL
);

CREATE TABLE action_catalogs (
    action_id                 TEXT PRIMARY KEY,
    action_name               TEXT NOT NULL UNIQUE,
    required_segment_id       TEXT REFERENCES segment_rules(segment_id) ON DELETE SET NULL,
    communication_channel     TEXT NOT NULL CHECK(communication_channel IN ('Email', 'SMS', 'Push Notification', 'Phone Call', 'Direct Mail', 'In-App')),
    cost_per_contact          REAL NOT NULL DEFAULT 0.0 CHECK(cost_per_contact >= 0.0),
    expected_conversion_rate  REAL NOT NULL CHECK(expected_conversion_rate BETWEEN 0.0 AND 1.0),
    suppression_period_days   INTEGER NOT NULL DEFAULT 14 CHECK(suppression_period_days >= 0),
    is_active                 INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    description               TEXT NOT NULL,
    created_at                TEXT NOT NULL
);

CREATE TABLE action_outcomes (
    outcome_id                TEXT PRIMARY KEY,
    action_id                 TEXT NOT NULL REFERENCES action_catalogs(action_id) ON DELETE RESTRICT,
    customer_id               TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    recommended_date          TEXT NOT NULL,
    executed_date             TEXT,
    execution_status          TEXT NOT NULL CHECK(execution_status IN ('Recommended', 'Suppressed', 'Sent', 'Failed', 'Delivered')),
    outcome_status            TEXT NOT NULL DEFAULT 'Pending' CHECK(outcome_status IN ('Pending', 'Opened', 'Clicked', 'Converted', 'Ignored', 'Unsubscribed')),
    attributed_order_id       TEXT REFERENCES orders(order_id) ON DELETE SET NULL,
    conversion_value          REAL NOT NULL DEFAULT 0.0 CHECK(conversion_value >= 0.0),
    attribution_confidence    REAL NOT NULL DEFAULT 1.0 CHECK(attribution_confidence BETWEEN 0.0 AND 1.0),
    recorded_at               TEXT NOT NULL
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_order_lines_order_id ON order_lines(order_id);
CREATE INDEX idx_order_lines_product_id ON order_lines(product_id);
CREATE INDEX idx_engagement_customer_id ON engagement_events(customer_id);
CREATE INDEX idx_engagement_timestamp ON engagement_events(event_timestamp);
CREATE INDEX idx_support_customer_id ON support_cases(customer_id);
CREATE INDEX idx_consents_customer_channel ON consents(customer_id, channel, is_active);
CREATE INDEX idx_memberships_customer_active ON segment_memberships(customer_id, is_active);
CREATE INDEX idx_memberships_segment_id ON segment_memberships(segment_id);
CREATE INDEX idx_outcomes_customer_action ON action_outcomes(customer_id, action_id);
CREATE INDEX idx_outcomes_attributed_order ON action_outcomes(attributed_order_id);
