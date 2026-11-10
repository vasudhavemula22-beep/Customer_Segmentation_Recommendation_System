# Explainable Customer Segmentation and Action Recommendation System

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-green.svg)](https://www.sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/Pytest-33%20Passed-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An explainable customer analytics and action recommendation platform built using Python, SQLite, and Streamlit. The system analyzes customer purchasing behavior, engagement, and service activity to perform RFM-based segmentation and generate actionable recommendations.

It also incorporates consent enforcement, communication suppression, conversion attribution, and anomaly detection to support transparent and auditable customer management.

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

Modern CRM systems face two important challenges:

1. **The Black-Box Problem:** Clustering algorithms can assign customers to mathematical groups without providing clear explanations that business users can understand.
2. **The Governance Problem:** Customer recommendations may ignore communication preferences, unresolved service complaints, or withdrawn consent.

This project provides an auditable, deterministic, rule-based customer segmentation and recommendation system. It generates human-readable explanations for customer segment assignments and recommended actions, supported by relational data integrity in SQLite.

---

## 2. Business Problem

Marketing and customer management teams can face several challenges:

- Sending irrelevant promotions to disengaged or dissatisfied customers.
- Offering promotions to customers with unresolved service complaints.
- Contacting customers who have withdrawn marketing consent.
- Incorrectly attributing purchases to marketing campaigns.
- Making customer segmentation decisions that are difficult to explain.

This system addresses these challenges through explainable segmentation, recommendation rules, consent enforcement, and anomaly detection.

---

## 3. Project Objectives

- Generate scalable synthetic customer data for up to **50,000 customers, 200,000 orders, and 1,000,000 engagement events** using a deterministic seed (`20261022`).
- Build an explainable RFM engine that assigns customers to mutually exclusive segments with human-readable explanations.
- Develop an action recommendation engine with service-ticket prioritization and communication suppression.
- Maintain customer and segment history using Slowly Changing Dimensions (SCD Type 2), where implemented.
- Inject and detect four mandatory anomaly scenarios using independent validation rules.
- Build an interactive Streamlit dashboard with Plotly visualizations.
- Evaluate system behavior through automated tests and measurable metrics.

---

## 4. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.13 |
| Database | SQLite 3, WAL Mode, Foreign Keys |
| Data Processing | Pandas, NumPy |
| Dashboard | Streamlit |
| Data Visualization | Plotly Express, Plotly Graph Objects |
| Testing | Pytest |
| Development Environment | Windows PowerShell |

---

## 5. System Architecture

```text
Customer_Segmentation_Recommendation_System/
│
├── app/
│   └── app.py                    # Streamlit dashboard
│
├── src/
│   ├── database/                 # Database connections and schema
│   ├── data_generation/          # Synthetic data generation
│   ├── segmentation/             # RFM calculations and segment rules
│   ├── recommendations/          # Action and consent rules
│   ├── anomalies/                 # Anomaly detection
│   ├── dashboard/                # Dashboard metric calculations
│   └── utils/                     # Validation and utility functions
│
├── data/
│   ├── raw/                       # Generated CSV files
│   ├── exports/                   # JSON exports
│   └── ground_truth/              # Benchmark data
│
├── database/
│   ├── schema.sql                 # Database schema
│   └── ecommerce_crm.db           # SQLite database
│
├── docs/
│   ├── data_dictionary.md
│   ├── er_diagram.md
│   ├── validation_summary.md
│   └── source_manifest.md
│
├── tests/                         # Automated tests
│
├── requirements.txt               # Project dependencies
├── README.md                      # Project documentation
└── LICENSE                        # MIT License
```

---

## 6. Database Schema & Entity Relationships

The system uses a relational SQLite database to organize customer, transaction, engagement, support, segmentation, recommendation, and outcome information.

Refer to the [Data Dictionary](docs/data_dictionary.md) and [ER Diagram](docs/er_diagram.md) for the detailed database structure and entity relationships.

---

## 7. RFM Segmentation Methodology

The system uses three key customer metrics:

- **Recency (R):** How recently a customer made a purchase.
- **Frequency (F):** How often a customer makes purchases.
- **Monetary (M):** How much a customer spends.

These metrics help identify customer behavior and assign customers to meaningful segments using explainable business rules.

---

## 8. Action Recommendation Engine & Rules

The recommendation engine uses customer segment information, purchase behavior, engagement activity, and service information to determine appropriate actions.

Recommendations are evaluated using eligibility rules, customer preferences, consent requirements, and suppression conditions.

Each recommendation should have an understandable reason explaining why the action was suggested or suppressed.

---

## 9. Consent Enforcement & Suppression Logic

The system checks customer consent and applicable communication preferences before allowing restricted marketing actions.

It also considers suppression conditions, such as unresolved support cases and communication restrictions, according to the implemented business rules.

---

## 10. The Four Mandatory Anomaly Scenarios

The anomaly detection component handles four important scenarios:

1. **Conflicting Segment Membership:** A customer is assigned to multiple mutually exclusive segments.
2. **Consent Violation:** An action violates the customer's applicable consent restrictions.
3. **Incorrect Return Calculation:** Returned amounts are not correctly deducted from customer spending.
4. **Wrong Outcome Attribution:** A conversion outcome is attributed to an incorrect action.

The detection process uses independent validation rules rather than relying only on the ground-truth benchmark data.

---

## 11. Measurable Evaluation Metrics

The project includes evaluation metrics to assess segmentation, recommendation behavior, anomaly detection, data quality, and system reliability.

Refer to the dashboard's **System Evaluation Metrics** section and the validation documentation for the available measurements.

---

## 12. Installation & Development Environment

### Prerequisites

- Python 3.13
- Git
- Windows PowerShell
- A code editor such as Visual Studio Code

### Clone the repository

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### Open the project folder

```powershell
cd Customer_Segmentation_Recommendation_System
```

### Create a virtual environment

```powershell
python -m venv .venv
```

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 13. PowerShell Execution Commands

Run the following commands from the project root directory.

| Task | Command |
|---|---|
| Check Python | `python --version` |
| Check pip | `python -m pip --version` |
| Activate environment | `.\.venv\Scripts\Activate.ps1` |
| Install dependencies | `pip install -r requirements.txt` |
| Run automated tests | `pytest -v` |

---

## 14. Generating Starter, Medium, and Full Datasets

The project supports configurable synthetic datasets for development and evaluation.

| Dataset | Customers | Orders | Engagement Events |
|---|---:|---:|---:|
| Starter | 100 | Configurable | Configurable |
| Medium | 5,000 | Configurable | Configurable |
| Full | 50,000 | 200,000 | 1,000,000 |

The data generator uses a fixed random seed (`20261022`) to support reproducibility.

Refer to the project's data generation instructions for the exact commands and available configuration options.

---

## 15. Running Automated Tests

Run the automated test suite using:

```powershell
pytest -v
```

The tests cover the implemented database operations, business rules, segmentation, recommendations, anomaly detection, and validation scenarios.

---

## 16. Launching the Streamlit Dashboard

From the project root directory, activate the virtual environment and run:

```powershell
streamlit run app/app.py
```

Streamlit will provide a local URL, usually:

```text
http://localhost:8501
```

Open this address in your browser to access the dashboard.

### Dashboard Sections

The application includes six main sections:

1. **Executive Overview** – Displays high-level customer, revenue, recommendation, and anomaly metrics.
2. **Customer 360° Explorer** – Allows users to explore individual customer information and activity.
3. **RFM Segmentation** – Displays customer segments and their associated RFM metrics.
4. **Action Recommendations** – Shows recommended and suppressed customer actions.
5. **Anomaly Detection & QA** – Displays detected data and business-rule anomalies.
6. **System Evaluation Metrics** – Presents available system performance and validation measurements.

---

## 17. Sample Outputs & Reports

The project includes supporting documentation and generated outputs, where available:

- Database schema and entity relationship documentation.
- Data dictionary.
- Synthetic data exports.
- Ground-truth benchmark data.
- Validation and evaluation reports.
- Interactive Streamlit dashboard.

---

## 18. Known Limitations

- The dataset is synthetic and does not represent actual customer records.
- Recommendation quality depends on the implemented business rules and generated data.
- Evaluation results on synthetic data should not be interpreted as real-world business performance.
- Production deployment would require additional security, privacy, monitoring, and scalability considerations.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
