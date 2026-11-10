# Entity Relationship Architecture

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : "places (1:N)"
    CUSTOMERS ||--o{ ENGAGEMENT_EVENTS : "generates (1:N)"
    CUSTOMERS ||--o{ SUPPORT_CASES : "opens (1:N)"
    CUSTOMERS ||--o{ CONSENTS : "grants/revokes (1:N)"
    CUSTOMERS ||--o{ SEGMENT_MEMBERSHIPS : "belongs to (1:N)"
    CUSTOMERS ||--o{ ACTION_OUTCOMES : "receives (1:N)"

    ORDERS ||--|{ ORDER_LINES : "contains (1:N)"
    ORDERS ||--o{ SUPPORT_CASES : "referenced by (0..1:N)"
    ORDERS ||--o{ ACTION_OUTCOMES : "attributed in (0..1:N)"

    PRODUCTS ||--o{ ORDER_LINES : "included in (1:N)"

    SEGMENT_RULES ||--o{ SEGMENT_MEMBERSHIPS : "defines (1:N)"
    SEGMENT_RULES ||--o{ ACTION_CATALOGS : "targets (0..1:N)"

    ACTION_CATALOGS ||--o{ ACTION_OUTCOMES : "tracks (1:N)"

    CUSTOMERS {
        string customer_id PK
        string first_name
        string last_name
        string email UK
        string phone
        string acquisition_channel
        string lifecycle_stage
        string created_at
        string updated_at
    }

    PRODUCTS {
        string product_id PK
        string product_name
        string category
        float base_price
        float cost
        int is_active
        string created_at
    }

    ORDERS {
        string order_id PK
        string customer_id FK
        string order_date
        string order_status
        string channel
        float subtotal_amount
        float discount_amount
        float tax_amount
        float total_amount
        float net_amount
        string created_at
    }

    ORDER_LINES {
        string order_line_id PK
        string order_id FK
        string product_id FK
        int quantity
        float unit_price
        float line_total
        int is_returned
        float return_amount
        string return_date
        string created_at
    }

    ENGAGEMENT_EVENTS {
        string event_id PK
        string customer_id FK
        string event_type
        string channel
        string event_timestamp
        string session_id
        string device_type
        string page_url
    }

    SUPPORT_CASES {
        string case_id PK
        string customer_id FK
        string order_id FK
        string case_category
        string priority
        string status
        float cost_amount
        string resolution_notes
        string opened_at
        string closed_at
    }

    CONSENTS {
        string consent_id PK
        string customer_id FK
        string channel
        string consent_type
        string status
        string effective_from
        string effective_to
        int is_active
        int version
        string updated_at
    }

    SEGMENT_RULES {
        string segment_id PK
        string segment_name UK
        string rfm_cell
        int min_recency_days
        int max_recency_days
        int min_frequency
        int max_frequency
        float min_monetary
        float max_monetary
        int is_exclusive
        int priority_order
        string description
        int is_active
        string created_at
    }

    SEGMENT_MEMBERSHIPS {
        string membership_id PK
        string segment_id FK
        string customer_id FK
        string assigned_date
        string valid_from
        string valid_to
        int is_active
        float confidence_score
        string assignment_reason
    }

    ACTION_CATALOGS {
        string action_id PK
        string action_name UK
        string required_segment_id FK
        string communication_channel
        float cost_per_contact
        float expected_conversion_rate
        int suppression_period_days
        int is_active
        string description
        string created_at
    }

    ACTION_OUTCOMES {
        string outcome_id PK
        string action_id FK
        string customer_id FK
        string recommended_date
        string executed_date
        string execution_status
        string outcome_status
        string attributed_order_id FK
        float conversion_value
        float attribution_confidence
        string recorded_at
    }
