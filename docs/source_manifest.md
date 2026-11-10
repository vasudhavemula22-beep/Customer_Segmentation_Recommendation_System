# Synthetic Data Source Manifest & Provenance

**Document Version:** 1.0.0  
**Generated On:** 2026-11-10 13:22:19  
**Master Random Seed:** `20261022`  
**Generator Source:** `src/data_generation/generator.py`  

---

## 1. Data Provenance & Lawful Use Declaration
- **100% Synthetically Generated:** All customer identities, telephone numbers, emails, addresses, orders, and service interactions in this system were deterministically generated using Python and NumPy PRNG algorithms.
- **Zero Real Personal Data (PII):** No live production data, customer personal identifiable information (PII), or confidential operational logs were collected, harvested, or processed.
- **Public Reference Inspiration:** Product taxonomies, retail pricing structures, and communication channel classifications are modeled on standard e-commerce retail benchmarks under fair-use schema inspiration.
- **Lawful Distribution:** This dataset and all associated code may be freely published, evaluated, and distributed under the MIT Open Source License without privacy or GDPR confidentiality restrictions.

---

## 2. Deterministic Reproducibility Proof

Every entity in this system is derived mathematically from the master seed `20261022`. Two consecutive generations yield bit-for-bit identical row counts, timestamps, and cryptographic checksums:

| Entity           |   Run 1 Count |   Run 2 Count | Run 1 SHA-256   | Run 2 SHA-256   | Verification     |
|------------------|---------------|---------------|-----------------|-----------------|------------------|
| Customers        |         1,000 |         1,000 | 059a2c62486d... | 059a2c62486d... | IDENTICAL (100%) |
| Products         |            50 |            50 | b85143ffa31b... | b85143ffa31b... | IDENTICAL (100%) |
| Orders           |         4,000 |         4,000 | 3db59cbc0c0a... | 3db59cbc0c0a... | IDENTICAL (100%) |
| OrderLines       |         6,727 |         6,727 | a8c067dff94d... | a8c067dff94d... | IDENTICAL (100%) |
| EngagementEvents |        20,000 |        20,000 | 00930063a264... | 00930063a264... | IDENTICAL (100%) |

---

## 3. Scalability Profiles Supported
1. **Starter Dataset:** 100 customers, 400 orders, 2,000 engagement events (Rapid local testing).
2. **Medium Dataset:** 5,000 customers, 20,000 orders, 100,000 engagement events.
3. **Full Scale Dataset:** 50,000 customers, 200,000 orders, 1,000,000 engagement events.
