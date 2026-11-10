# System Data Dictionary

## 1. Table: `customers`
Master registry for individual customer entities.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | TEXT | NO | PK | `CUS-000001` to `CUS-999999` | Dimensionless | Unique | Regex match `^CUS-\d{6}$` |
| `first_name` | TEXT | NO | None | Text | Dimensionless | Non-unique | Length >= 1 |
| `last_name` | TEXT | NO | None | Text | Dimensionless | Non-unique | Length >= 1 |
| `email` | TEXT | NO | None | Valid email address | Dimensionless | Unique | Contains `@` and `.` |
| `phone` | TEXT | YES | None | E.164 phone string | Dimensionless | Non-unique | Optional |
| `acquisition_channel` | TEXT | NO | None | `'Organic'`, `'Paid Search'`, `'Social Media'`, `'Email Referral'`, `'Direct'` | Dimensionless | Non-unique | CHECK enum |
| `lifecycle_stage` | TEXT | NO | None | `'Prospect'`, `'Active'`, `'Dormant'`, `'Churned'` | Dimensionless | Non-unique | CHECK enum |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string (`YYYY-MM-DD HH:MM:SS`) | Timestamp | Non-unique | Valid timestamp |
| `updated_at` | TEXT | NO | None | ISO-8601 UTC string (`YYYY-MM-DD HH:MM:SS`) | Timestamp | Non-unique | `>= created_at` |

---

## 2. Table: `products`
Catalog of commercial merchandise.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | TEXT | NO | PK | `PRD-000001` to `PRD-999999` | Dimensionless | Unique | Regex `^PRD-\d{6}$` |
| `product_name` | TEXT | NO | None | Free text | Dimensionless | Non-unique | Length >= 1 |
| `category` | TEXT | NO | None | `'Electronics'`, `'Apparel'`, `'Home & Kitchen'`, `'Beauty'`, `'Sports'` | Dimensionless | Non-unique | CHECK enum |
| `base_price` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `base_price >= 0.0` |
| `cost` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `cost >= 0.0` |
| `is_active` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_active IN (0, 1)` |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 3. Table: `orders`
Header records for sales transactions.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | TEXT | NO | PK | `ORD-2026-000001` to `ORD-2026-999999` | Dimensionless | Unique | Regex `^ORD-\d{4}-\d{6}$` |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | FK constraint |
| `order_date` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `order_status` | TEXT | NO | None | `'Pending'`, `'Processing'`, `'Shipped'`, `'Delivered'`, `'Cancelled'`, `'Returned'` | Dimensionless | Non-unique | CHECK enum |
| `channel` | TEXT | NO | None | `'Web'`, `'Mobile App'`, `'In-Store'`, `'Affiliate'` | Dimensionless | Non-unique | CHECK enum |
| `subtotal_amount`| REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `subtotal_amount >= 0.0` |
| `discount_amount`| REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `discount_amount >= 0.0` |
| `tax_amount` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `tax_amount >= 0.0` |
| `total_amount` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | Subtotal - Discount + Tax |
| `net_amount` | REAL | NO | None | Any real value | USD ($) | Non-unique | Total - Returns |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 4. Table: `order_lines`
Itemized inventory line records for orders.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_line_id` | TEXT | NO | PK | `ORL-2026-000001` to `ORL-2026-999999` | Dimensionless | Unique | Regex `^ORL-\d{4}-\d{6}$` |
| `order_id` | TEXT | NO | FK | Matches `orders.order_id` | Dimensionless | Non-unique | ON DELETE CASCADE |
| `product_id` | TEXT | NO | FK | Matches `products.product_id` | Dimensionless | Non-unique | ON DELETE RESTRICT |
| `quantity` | INTEGER | NO | None | Integer > 0 | Items | Non-unique | `quantity > 0` |
| `unit_price` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `unit_price >= 0.0` |
| `line_total` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `quantity * unit_price` |
| `is_returned` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_returned IN (0, 1)` |
| `return_amount` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `return_amount >= 0.0` |
| `return_date` | TEXT | YES | None | ISO-8601 UTC string or NULL | Timestamp | Non-unique | Required if `is_returned = 1` |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 5. Table: `engagement_events`
High-frequency behavioural interaction logs.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | TEXT | NO | PK | `EVT-2026-000001` to `EVT-2026-999999` | Dimensionless | Unique | Regex `^EVT-\d{4}-\d{6}$` |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | ON DELETE CASCADE |
| `event_type` | TEXT | NO | None | `'page_view'`, `'product_view'`, `'add_to_cart'`, `'email_open'`, `'email_click'`, `'app_login'`, `'search'` | Dimensionless | Non-unique | CHECK enum |
| `channel` | TEXT | NO | None | `'Web'`, `'Mobile App'`, `'Email'`, `'SMS'`, `'Push'` | Dimensionless | Non-unique | CHECK enum |
| `event_timestamp`| TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `session_id` | TEXT | NO | None | Session token string | Dimensionless | Non-unique | Length >= 1 |
| `device_type` | TEXT | NO | None | `'Desktop'`, `'Mobile'`, `'Tablet'`, `'Other'` | Dimensionless | Non-unique | CHECK enum |
| `page_url` | TEXT | YES | None | String path or URL | Dimensionless | Non-unique | Optional |

---

## 6. Table: `support_cases`
Customer service tickets and support intervention expenditures.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `case_id` | TEXT | NO | PK | `CAS-2026-000001` to `CAS-2026-999999` | Dimensionless | Unique | Regex `^CAS-\d{4}-\d{6}$` |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | ON DELETE RESTRICT |
| `order_id` | TEXT | YES | FK | Matches `orders.order_id` or NULL | Dimensionless | Non-unique | Optional relationship |
| `case_category` | TEXT | NO | None | `'Billing'`, `'Shipping'`, `'Product Defect'`, `'Return Request'`, `'General Inquiry'` | Dimensionless | Non-unique | CHECK enum |
| `priority` | TEXT | NO | None | `'Low'`, `'Medium'`, `'High'`, `'Critical'` | Dimensionless | Non-unique | CHECK enum |
| `status` | TEXT | NO | None | `'Open'`, `'In Progress'`, `'Resolved'`, `'Closed'` | Dimensionless | Non-unique | CHECK enum |
| `cost_amount` | REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `cost_amount >= 0.0` |
| `resolution_notes`| TEXT | YES | None | String | Dimensionless | Non-unique | Optional |
| `opened_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `closed_at` | TEXT | YES | None | ISO-8601 UTC string or NULL | Timestamp | Non-unique | `>= opened_at` |

---

## 7. Table: `consents`
Explicit customer marketing permissions and legal opt-in audit log.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `consent_id` | TEXT | NO | PK | `CON-000001` to `CON-999999` | Dimensionless | Unique | Regex `^CON-\d{6}$` |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | ON DELETE CASCADE |
| `channel` | TEXT | NO | None | `'Email'`, `'SMS'`, `'Push Notification'`, `'Phone Call'`, `'Direct Mail'` | Dimensionless | Non-unique | CHECK enum |
| `consent_type` | TEXT | NO | None | `'Marketing'`, `'Transactional'`, `'Data Processing'`, `'Analytics'` | Dimensionless | Non-unique | CHECK enum |
| `status` | TEXT | NO | None | `'Opted In'`, `'Opted Out'`, `'Pending'` | Dimensionless | Non-unique | CHECK enum |
| `effective_from` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `effective_to` | TEXT | YES | None | ISO-8601 UTC string or NULL | Timestamp | Non-unique | NULL indicates active |
| `is_active` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_active IN (0, 1)` |
| `version` | INTEGER | NO | None | Integer >= 1 | Version counter | Non-unique | `version > 0` |
| `updated_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 8. Table: `segment_rules`
Definitive RFM thresholds and business classification metadata.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `segment_id` | TEXT | NO | PK | `SEG-2026-000001` to `SEG-2026-999999` | Dimensionless | Unique | Regex `^SEG-\d{4}-\d{6}$` |
| `segment_name` | TEXT | NO | None | Business tag (e.g. `'Champions'`) | Dimensionless | Unique | UNIQUE constraint |
| `rfm_cell` | TEXT | YES | None | Text pattern (e.g. `'R5-F5-M5'`) | Dimensionless | Non-unique | Optional |
| `min_recency_days`| INTEGER | YES | None | Integer >= 0 or NULL | Days | Non-unique | `>= 0` |
| `max_recency_days`| INTEGER | YES | None | Integer >= 0 or NULL | Days | Non-unique | `>= min_recency_days` |
| `min_frequency` | INTEGER | YES | None | Integer >= 0 or NULL | Orders count | Non-unique | `>= 0` |
| `max_frequency` | INTEGER | YES | None | Integer >= 0 or NULL | Orders count | Non-unique | `>= min_frequency` |
| `min_monetary` | REAL | YES | None | Real >= 0.0 or NULL | USD ($) | Non-unique | `>= 0.0` |
| `max_monetary` | REAL | YES | None | Real >= 0.0 or NULL | USD ($) | Non-unique | `>= min_monetary` |
| `is_exclusive` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_exclusive IN (0, 1)` |
| `priority_order` | INTEGER | NO | None | Integer >= 1 | Dimensionless | Non-unique | Lower number = higher priority |
| `description` | TEXT | NO | None | Explanation text | Dimensionless | Non-unique | Length >= 1 |
| `is_active` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_active IN (0, 1)` |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 9. Table: `segment_memberships`
Bridge table linking Customers and Segments over time (SCD Type 2).

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `membership_id` | TEXT | NO | PK | `MEM-SEG-XXXXXX-CUS-XXXXXX` | Dimensionless | Unique | Deterministic compound PK |
| `segment_id` | TEXT | NO | FK | Matches `segment_rules.segment_id` | Dimensionless | Non-unique | ON DELETE RESTRICT |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | ON DELETE CASCADE |
| `assigned_date` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `valid_from` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `valid_to` | TEXT | YES | None | ISO-8601 UTC string or NULL | Timestamp | Non-unique | NULL indicates active |
| `is_active` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_active IN (0, 1)` |
| `confidence_score`| REAL | NO | None | Float 0.00 to 1.00 | Probability | Non-unique | `BETWEEN 0.0 AND 1.0` |
| `assignment_reason`| TEXT | NO | None | Explanatory text | Dimensionless | Non-unique | Length >= 1 |

---

## 10. Table: `action_catalogs`
Dictionary of authorized interventions and communication actions.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `action_id` | TEXT | NO | PK | `ACTN-2026-000001` to `ACTN-2026-999999` | Dimensionless | Unique | Regex `^ACTN-\d{4}-\d{6}$` |
| `action_name` | TEXT | NO | None | Text | Dimensionless | Unique | UNIQUE constraint |
| `required_segment_id`| TEXT | YES | FK | Matches `segment_rules.segment_id` | Dimensionless | Non-unique | ON DELETE SET NULL |
| `communication_channel`| TEXT| NO | None | `'Email'`, `'SMS'`, `'Push Notification'`, `'Phone Call'`, `'Direct Mail'`, `'In-App'` | Dimensionless | Non-unique | CHECK enum |
| `cost_per_contact`| REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `cost_per_contact >= 0.0` |
| `expected_conversion_rate`| REAL | NO | None | Float 0.00 to 1.00 | Rate | Non-unique | `BETWEEN 0.0 AND 1.0` |
| `suppression_period_days`| INTEGER | NO | None | Value >= 0 | Days | Non-unique | `suppression_period_days >= 0` |
| `is_active` | INTEGER | NO | None | `0`, `1` | Boolean Flag | Non-unique | CHECK `is_active IN (0, 1)` |
| `description` | TEXT | NO | None | Explanatory text | Dimensionless | Non-unique | Length >= 1 |
| `created_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |

---

## 11. Table: `action_outcomes`
Execution ledger of recommendations and associated revenue conversions.

| Column Name | SQLite Type | Nullable | Key | Allowed Values / Format | Units | Uniqueness | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `outcome_id` | TEXT | NO | PK | `OUT-2026-000001` to `OUT-2026-999999` | Dimensionless | Unique | Regex `^OUT-\d{4}-\d{6}$` |
| `action_id` | TEXT | NO | FK | Matches `action_catalogs.action_id` | Dimensionless | Non-unique | ON DELETE RESTRICT |
| `customer_id` | TEXT | NO | FK | Matches `customers.customer_id` | Dimensionless | Non-unique | ON DELETE CASCADE |
| `recommended_date`| TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
| `executed_date` | TEXT | YES | None | ISO-8601 UTC string or NULL | Timestamp | Non-unique | Optional |
| `execution_status`| TEXT | NO | None | `'Recommended'`, `'Suppressed'`, `'Sent'`, `'Failed'`, `'Delivered'` | Dimensionless | Non-unique | CHECK enum |
| `outcome_status` | TEXT | NO | None | `'Pending'`, `'Opened'`, `'Clicked'`, `'Converted'`, `'Ignored'`, `'Unsubscribed'` | Dimensionless | Non-unique | CHECK enum |
| `attributed_order_id`| TEXT | YES | FK | Matches `orders.order_id` or NULL | Dimensionless | Non-unique | Optional attribution |
| `conversion_value`| REAL | NO | None | Value >= 0.00 | USD ($) | Non-unique | `conversion_value >= 0.0` |
| `attribution_confidence`| REAL | NO | None | Float 0.00 to 1.00 | Probability | Non-unique | `BETWEEN 0.0 AND 1.0` |
| `recorded_at` | TEXT | NO | None | ISO-8601 UTC string | Timestamp | Non-unique | Valid timestamp |
