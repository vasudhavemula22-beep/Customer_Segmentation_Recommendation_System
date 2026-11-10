"""
Synthetic Data Generation Engine.
Produces realistic, deterministic datasets with full relational and arithmetic consistency.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import numpy as np

from src.data_generation.config import (
    ACQUISITION_CHANNELS,
    CASE_CATEGORIES,
    CASE_PRIORITIES,
    CASE_STATUSES,
    CONSENT_CHANNELS,
    CONSENT_TYPES,
    DEVICE_TYPES,
    EMAIL_DOMAINS,
    EVENT_CHANNELS,
    EVENT_TYPES,
    FIRST_NAMES,
    LAST_NAMES,
    LIFECYCLE_STAGES,
    ORDER_CHANNELS,
    ORDER_STATUSES,
    PRODUCT_CATEGORIES,
    RANDOM_SEED,
    ScaleConfig,
)


class SyntheticDataGenerator:
    """Deterministic, streaming-compatible generator for the CRM system."""

    def __init__(self, config: ScaleConfig, seed: int = RANDOM_SEED) -> None:
        self.config = config
        self.seed = seed
        self.py_rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        
        # Simulation anchor date: 2026-10-22
        self.anchor_date = datetime(2026, 10, 22, 12, 0, 0)
        self.history_start_date = datetime(2025, 1, 1, 0, 0, 0)
        self.total_days = (self.anchor_date - self.history_start_date).days

        # In-memory parent lookups for referential integrity
        self.customer_ids: List[str] = []
        self.customer_created_dates: Dict[str, datetime] = {}
        self.customer_archetypes: Dict[str, str] = {}
        self.product_catalog: List[Dict[str, Any]] = []
        self.generated_orders: List[Dict[str, Any]] = []

    def _format_id(self, prefix: str, number: int, width: int = 6) -> str:
        return f"{prefix}-{str(number).zfill(width)}"

    def _format_order_id(self, year: int, number: int) -> str:
        return f"ORD-{year}-{str(number).zfill(6)}"

    def _format_order_line_id(self, year: int, number: int) -> str:
        return f"ORL-{year}-{str(number).zfill(6)}"

    def _format_event_id(self, year: int, number: int) -> str:
        return f"EVT-{year}-{str(number).zfill(6)}"

    def _format_case_id(self, year: int, number: int) -> str:
        return f"CAS-{year}-{str(number).zfill(6)}"

    def _random_date_between(self, start: datetime, end: datetime) -> datetime:
        delta = end - start
        random_seconds = self.py_rng.randint(0, max(0, int(delta.total_seconds())))
        return start + timedelta(seconds=random_seconds)

    # --------------------------------------------------------------------------
    # 1. CUSTOMERS
    # --------------------------------------------------------------------------
    def generate_customers(self) -> List[Dict[str, Any]]:
        customers: List[Dict[str, Any]] = []
        
        # Archetype distribution: 60% Active, 20% Dormant, 15% Prospect, 5% Churned
        archetype_choices = ["Active", "Dormant", "Prospect", "Churned"]
        archetype_weights = [0.60, 0.20, 0.15, 0.05]

        for i in range(1, self.config.customers + 1):
            cid = self._format_id("CUS", i)
            self.customer_ids.append(cid)

            archetype = self.py_rng.choices(archetype_choices, weights=archetype_weights, k=1)[0]
            self.customer_archetypes[cid] = archetype

            first_name = self.py_rng.choice(FIRST_NAMES)
            last_name = self.py_rng.choice(LAST_NAMES)
            domain = self.py_rng.choice(EMAIL_DOMAINS)
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@{domain}"
            
            phone = f"+1-{self.py_rng.randint(200, 999)}-{self.py_rng.randint(100, 999)}-{self.py_rng.randint(1000, 9999)}"
            channel = self.py_rng.choice(ACQUISITION_CHANNELS)

            if archetype == "Prospect":
                # Registered within the last 30 days
                created_dt = self._random_date_between(self.anchor_date - timedelta(days=30), self.anchor_date)
            elif archetype == "Dormant":
                # Registered 300 to 600 days ago
                created_dt = self._random_date_between(self.history_start_date, self.anchor_date - timedelta(days=200))
            else:
                # Active or Churned
                created_dt = self._random_date_between(self.history_start_date, self.anchor_date - timedelta(days=60))

            updated_dt = self._random_date_between(created_dt, self.anchor_date)
            self.customer_created_dates[cid] = created_dt

            customers.append({
                "customer_id": cid,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "acquisition_channel": channel,
                "lifecycle_stage": archetype,
                "created_at": created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": updated_dt.strftime("%Y-%m-%d %H:%M:%S")
            })

        return customers

    # --------------------------------------------------------------------------
    # 2. PRODUCTS
    # --------------------------------------------------------------------------
    def generate_products(self) -> List[Dict[str, Any]]:
        products: List[Dict[str, Any]] = []
        flat_catalog: List[Tuple[str, str, float, float]] = []

        for category, item_list in PRODUCT_CATEGORIES.items():
            for item_name, base_price, cost in item_list:
                flat_catalog.append((category, item_name, base_price, cost))

        for i in range(1, self.config.products + 1):
            pid = self._format_id("PRD", i)
            base_category, base_name, base_price, base_cost = flat_catalog[(i - 1) % len(flat_catalog)]
            
            variant_suffix = f" Model {chr(65 + (i // len(flat_catalog)) % 26)}" if i > len(flat_catalog) else ""
            name = f"{base_name}{variant_suffix}"
            price_multiplier = self.py_rng.uniform(0.90, 1.15)
            final_price = round(base_price * price_multiplier, 2)
            final_cost = round(base_cost * price_multiplier, 2)

            prod = {
                "product_id": pid,
                "product_name": name,
                "category": base_category,
                "base_price": final_price,
                "cost": final_cost,
                "is_active": 1,
                "created_at": self.history_start_date.strftime("%Y-%m-%d %H:%M:%S")
            }
            products.append(prod)
            self.product_catalog.append(prod)

        return products

    # --------------------------------------------------------------------------
    # 3 & 4. ORDERS AND ORDER LINES
    # --------------------------------------------------------------------------
    def generate_orders_and_lines(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        orders: List[Dict[str, Any]] = []
        order_lines: List[Dict[str, Any]] = []

        active_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Active"]
        dormant_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Dormant"]
        prospect_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Prospect"]
        churned_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Churned"]

        order_line_counter = 1

        for ord_idx in range(1, self.config.orders + 1):
            order_id = self._format_order_id(2026, ord_idx)

            roll = self.py_rng.random()
            if roll < 0.75 and active_customers:
                cid = self.py_rng.choice(active_customers)
            elif roll < 0.88 and dormant_customers:
                cid = self.py_rng.choice(dormant_customers)
            elif roll < 0.96 and prospect_customers:
                cid = self.py_rng.choice(prospect_customers)
            elif churned_customers:
                cid = self.py_rng.choice(churned_customers)
            else:
                cid = self.py_rng.choice(self.customer_ids)

            archetype = self.customer_archetypes[cid]
            cus_created = self.customer_created_dates[cid]

            if archetype == "Dormant":
                order_dt = self._random_date_between(cus_created, self.anchor_date - timedelta(days=180))
            elif archetype == "Prospect":
                order_dt = self._random_date_between(cus_created, self.anchor_date)
            else:
                order_dt = self._random_date_between(cus_created, self.anchor_date)

            num_lines = self.py_rng.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05], k=1)[0]
            selected_products = self.py_rng.sample(self.product_catalog, k=min(num_lines, len(self.product_catalog)))

            subtotal_amount = 0.0
            order_return_amount = 0.0
            has_return = False
            lines_for_this_order = []

            for prod in selected_products:
                line_id = self._format_order_line_id(2026, order_line_counter)
                order_line_counter += 1

                quantity = self.py_rng.choices([1, 2, 3], weights=[0.80, 0.15, 0.05], k=1)[0]
                unit_price = prod["base_price"]
                line_total = round(quantity * unit_price, 2)
                subtotal_amount += line_total

                is_returned = 1 if self.py_rng.random() < 0.08 else 0
                return_amount = line_total if is_returned == 1 else 0.0
                return_date = None

                if is_returned == 1:
                    has_return = True
                    order_return_amount += return_amount
                    return_dt = order_dt + timedelta(days=self.py_rng.randint(2, 14))
                    if return_dt > self.anchor_date:
                        return_dt = self.anchor_date
                    return_date = return_dt.strftime("%Y-%m-%d %H:%M:%S")

                line_record = {
                    "order_line_id": line_id,
                    "order_id": order_id,
                    "product_id": prod["product_id"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                    "is_returned": is_returned,
                    "return_amount": return_amount,
                    "return_date": return_date,
                    "created_at": order_dt.strftime("%Y-%m-%d %H:%M:%S")
                }
                order_lines.append(line_record)
                lines_for_this_order.append(line_record)

            subtotal_amount = round(subtotal_amount, 2)
            discount_amount = round(subtotal_amount * 0.10, 2) if self.py_rng.random() < 0.15 else 0.0
            taxable = max(0.0, subtotal_amount - discount_amount)
            tax_amount = round(taxable * 0.08, 2)
            total_amount = round(taxable + tax_amount, 2)
            net_amount = round(total_amount - order_return_amount, 2)

            if has_return and len(lines_for_this_order) == 1 and lines_for_this_order[0]["is_returned"] == 1:
                status = "Returned"
            else:
                status = self.py_rng.choices(ORDER_STATUSES, weights=[0.80, 0.10, 0.04, 0.03, 0.03], k=1)[0]

            order_record = {
                "order_id": order_id,
                "customer_id": cid,
                "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "order_status": status,
                "channel": self.py_rng.choice(ORDER_CHANNELS),
                "subtotal_amount": subtotal_amount,
                "discount_amount": discount_amount,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "net_amount": net_amount,
                "created_at": order_dt.strftime("%Y-%m-%d %H:%M:%S")
            }
            orders.append(order_record)
            self.generated_orders.append(order_record)

        return orders, order_lines

    # --------------------------------------------------------------------------
    # 5. ENGAGEMENT EVENTS
    # --------------------------------------------------------------------------
    def generate_engagement_events(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []

        active_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Active"]
        dormant_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Dormant"]
        prospect_customers = [c for c in self.customer_ids if self.customer_archetypes[c] == "Prospect"]

        for evt_idx in range(1, self.config.engagement_events + 1):
            event_id = self._format_event_id(2026, evt_idx)

            roll = self.py_rng.random()
            if roll < 0.80 and active_customers:
                cid = self.py_rng.choice(active_customers)
            elif roll < 0.90 and prospect_customers:
                cid = self.py_rng.choice(prospect_customers)
            elif dormant_customers:
                cid = self.py_rng.choice(dormant_customers)
            else:
                cid = self.py_rng.choice(self.customer_ids)

            archetype = self.customer_archetypes[cid]
            cus_created = self.customer_created_dates[cid]

            if archetype == "Dormant":
                event_dt = self._random_date_between(cus_created, self.anchor_date - timedelta(days=180))
            else:
                event_dt = self._random_date_between(cus_created, self.anchor_date)

            session_id = f"SES-{self.py_rng.randint(100000, 999999)}"
            event_type = self.py_rng.choice(EVENT_TYPES)
            channel = self.py_rng.choice(EVENT_CHANNELS)
            device = self.py_rng.choice(DEVICE_TYPES)
            page_url = f"/shop/{self.py_rng.choice(list(PRODUCT_CATEGORIES.keys())).lower()}"

            events.append({
                "event_id": event_id,
                "customer_id": cid,
                "event_type": event_type,
                "channel": channel,
                "event_timestamp": event_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": session_id,
                "device_type": device,
                "page_url": page_url
            })

        return events

    # --------------------------------------------------------------------------
    # 6. SUPPORT CASES
    # --------------------------------------------------------------------------
    def generate_support_cases(self) -> List[Dict[str, Any]]:
        cases: List[Dict[str, Any]] = []

        num_high_cost = max(2, int(len(self.customer_ids) * 0.05))
        high_cost_customers = set(self.py_rng.sample(self.customer_ids, k=num_high_cost))

        customer_to_orders: Dict[str, List[str]] = {}
        for ord_rec in self.generated_orders:
            customer_to_orders.setdefault(ord_rec["customer_id"], []).append(ord_rec["order_id"])

        for case_idx in range(1, self.config.support_cases + 1):
            case_id = self._format_case_id(2026, case_idx)

            if self.py_rng.random() < 0.40 and high_cost_customers:
                cid = self.py_rng.choice(list(high_cost_customers))
                cost_amount = round(self.py_rng.uniform(120.0, 350.0), 2)
                priority = self.py_rng.choice(["High", "Critical"])
            else:
                cid = self.py_rng.choice(self.customer_ids)
                cost_amount = round(self.py_rng.uniform(10.0, 45.0), 2)
                priority = self.py_rng.choice(CASE_PRIORITIES)

            cus_created = self.customer_created_dates[cid]
            opened_dt = self._random_date_between(cus_created, self.anchor_date)

            status = self.py_rng.choice(CASE_STATUSES)
            closed_at = None
            if status in ["Resolved", "Closed"]:
                closed_dt = opened_dt + timedelta(days=self.py_rng.randint(1, 5))
                if closed_dt > self.anchor_date:
                    closed_dt = self.anchor_date
                closed_at = closed_dt.strftime("%Y-%m-%d %H:%M:%S")

            available_orders = customer_to_orders.get(cid, [])
            order_id = self.py_rng.choice(available_orders) if (available_orders and self.py_rng.random() < 0.60) else None

            cases.append({
                "case_id": case_id,
                "customer_id": cid,
                "order_id": order_id,
                "case_category": self.py_rng.choice(CASE_CATEGORIES),
                "priority": priority,
                "status": status,
                "cost_amount": cost_amount,
                "resolution_notes": f"Standard remediation performed for {priority} ticket.",
                "opened_at": opened_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "closed_at": closed_at
            })

        return cases

    # --------------------------------------------------------------------------
    # 7. CONSENTS
    # --------------------------------------------------------------------------
    def generate_consents(self) -> List[Dict[str, Any]]:
        consents: List[Dict[str, Any]] = []
        consent_counter = 1

        for cid in self.customer_ids:
            cus_created = self.customer_created_dates[cid]

            for channel in CONSENT_CHANNELS:
                consent_id = self._format_id("CON", consent_counter)
                consent_counter += 1

                is_opted_out = self.py_rng.random() < 0.20

                if is_opted_out:
                    status = "Opted Out"
                    effective_from_dt = cus_created + timedelta(days=self.py_rng.randint(15, 90))
                    if effective_from_dt > self.anchor_date:
                        effective_from_dt = self.anchor_date
                    version = 2
                else:
                    status = "Opted In"
                    effective_from_dt = cus_created
                    version = 1

                consents.append({
                    "consent_id": consent_id,
                    "customer_id": cid,
                    "channel": channel,
                    "consent_type": "Marketing",
                    "status": status,
                    "effective_from": effective_from_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "effective_to": None,
                    "is_active": 1,
                    "version": version,
                    "updated_at": effective_from_dt.strftime("%Y-%m-%d %H:%M:%S")
                })

        return consents
