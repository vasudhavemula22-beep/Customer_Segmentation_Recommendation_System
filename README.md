
# Explainable Customer Segmentation and Action Recommendation System

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/SQLite-WAL%20Mode-green.svg)](https://www.sqlite.org/)
[![Dashboard](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/Pytest-33%20Passed-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, explainable customer analytics and action recommendation platform built with Python, SQLite, and Streamlit. The system combines multi-dimensional RFM scoring, legal consent enforcement, communication suppression, and closed-loop conversion attribution with an independent anomaly detection engine that identifies four mandatory negative scenarios with 100% Precision and Recall.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Business Problem](#2-business-problem)
3. [Project Objectives](#3-project-objectives)
4. [Technology Stack](#4-technology-stack)
5. [System Architecture](#5-system-architecture)
6. [Database Schema & Entity Relationships](#6-database-schema--entity-relationships)
7. [RFM Segmentation Methodology](#7-rfm-segmentation-methodology)
8. [Action Recommendation Engine & Rules](#8-action-recommendation-engine--rules)
9. [Consent Enforcement & Suppression Logic](#9-consent-enforcement--suppression-logic)
10. [The Four Mandatory Anomaly Scenarios](#10-the-four-mandatory-anomaly-scenarios)
11. [Measurable Evaluation Metrics](#11-measurable-evaluation-metrics)
12. [Installation & Development Environment](#12-installation--development-environment)
13. [PowerShell Execution Commands](#13-powershell-execution-commands)
14. [Generating Starter, Medium, and Full Datasets](#14-generating-starter-medium-and-full-datasets)
15. [Running Automated Tests](#15-running-automated-tests)
16. [Launching the Streamlit Dashboard](#16-launching-the-streamlit-dashboard)
17. [Sample Outputs & Reports](#17-sample-outputs--reports)
18. [Known Limitations](#18-known-limitations)

---

## 1. Project Overview
Modern CRM systems struggle with two key problems:
1. **The "Black-Box" Problem:** Machine learning clustering algorithms (e.g., K-Means) assign customers to mathematical clusters that commercial stakeholders cannot explain.
2. **The Governance Problem:** Recommendations often violate communication frequency limits, disregard unresolved service tickets, or breach customer legal opt-out preferences.

This project delivers an **auditable, deterministic, rule-based segmentation and recommendation engine** that produces natural-language explanations for every segment assignment and intervention, backed by strict relational integrity in SQLite.

---

## 2. Business Problem
Marketing teams routinely waste budget by:
- Bombarding disengaged or dissatisfied customers with irrelevant promotions.
- Sending marketing offers to customers with open, unresolved service complaints.
- Violating data privacy regulations (GDPR, CAN-SPAM, TCPA) by contacting users who have withdrawn consent.
- Misattributing sales conversions to campaigns that occurred after the purchase.

---

## 3. Project Objectives
- Generate scalable, realistic synthetic customer data up to **50,000 customers, 200,000 orders, and 1,000,000 events** with a deterministic seed (`20261022`).
- Build an **explainable RFM engine** that assigns customers into mutually exclusive segments with human-readable rationales.
- Build an **action recommendation engine** with service ticket prioritization and contact suppression.
- Preserve complete lifecycle history using **Slowly Changing Dimensions (SCD Type 2)**.
- Inject and detect **four mandatory anomaly scenarios** using independent validation rules without ground-truth leakage.
- Provide an interactive multi-view **Streamlit dashboard** with Plotly visual analytics.

---

## 4. Technology Stack
- **Language:** Python 3.13
- **Database Engine:** SQLite 3 (WAL Journal Mode, Strict Foreign Keys)
- **Data Engineering:** Pandas 2.2+, NumPy 2.0+
- **Interactive UI:** Streamlit 1.38+
- **Visual Analytics:** Plotly Express & Plotly Graph Objects 5.24+
- **Quality Assurance:** Pytest 8.3+ (33 automated unit and end-to-end integration tests)
- **Environment:** Windows PowerShell, UTF-8 encoding

---

## 5. System Architecture
```text
Customer_Segmentation_Recommendation_System/
├── app/                          # Streamlit Analytical Application
│   └── app.py                    # Multi-view dashboard entry point
├── src/                          # Core Python Packages
│   ├── database/                 # Connection management & schema execution
│   ├── data_generation/          # Synthetic generator & taxonomy configs
│   ├── segmentation/             # RFM calculator & explainable rules engine
│   ├── recommendations/          # Action catalog, consent & suppression rules
│   ├── anomalies/                # Attribution tracker & 4 anomaly detectors
│   ├── dashboard/                # Metric aggregators feeding Streamlit
│   └── utils/                    # Validation summary & reproducibility manifest
├── data/                         # Data Stage Storage
│   ├── raw/                      # Generated CSV files
│   ├── exports/                  # Standard JSON exports
│   └── ground_truth/             # Isolated benchmark files (ground_truth.json)
├── database/                     # SQLite binary and DDL schema
│   ├── schema.sql                # 11-entity relational DDL
│   └── ecommerce_crm.db          # Active database file
├── docs/                         # Project Documentation
│   ├── data_dictionary.md        # Comprehensive 11-table dictionary
│   ├── er_diagram.md             # Mermaid relationship diagram
│   ├── validation_summary.md     # 12-point audit sign-off
│   └── source_manifest.md        # Reproducibility & provenance proof
├── tests/                        # Automated Pytest Suite (33 tests)
├── requirements.txt              # Pinned project dependencies
└── README.md                     # Master system documentation