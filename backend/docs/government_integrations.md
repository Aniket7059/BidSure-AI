# Government & GeM Verification Integration Architecture

This document describes the **BidSure AI Backend Architecture** for external government portal and GeM procurement verification connectors, developed for SIH 2026 Problem Statement 26100.

---

## 1. Provenance & Source Mode Taxonomy

BidSure AI enforces a strict four-level provenance taxonomy for all verification outputs:

| Source Mode | Description | Production Guarantee |
| :--- | :--- | :--- |
| **`OFFICIAL_API`** | Direct connection to official government API gateways (e.g. MCA21, DigiLocker, EPFO). | Requires official agency credentials & whitelisted IP. |
| **`AUTHORIZED_PROVIDER`** | Connection via authorized GSP/ASP or API aggregator (e.g. GSTN GSP, NSDL PAN). | Requires contract with authorized provider & API key. |
| **`MANUAL`** | Human-in-the-loop manual verification recorded by authorized Procurement Officer. | Immutable audit log event with officer ID & reference notes. |
| **`SYNTHETIC`** | Deterministic mock adapter for development, testing, and demonstration. | Explicitly flagged `SYNTHETIC`; **NEVER** claimed as live government data. |

---

## 2. Integration Classification Matrix

| Target Source / Portal | Classification | Implemented Adapter | Operational Availability |
| :--- | :--- | :--- | :--- |
| **GST / GSTN Portal** | `AUTHORIZED_PROVIDER` | `LiveGSTAdapter` | Configuration Required (`GST_API_KEY`) |
| **Income Tax / PAN (NSDL)** | `AUTHORIZED_PROVIDER` | `LivePANAdapter` | Configuration Required (`PAN_API_KEY`) |
| **Udyam MSME Portal** | `AUTHORIZED_PROVIDER` | `LiveUdyamAdapter` | Configuration Required (`UDYAM_API_KEY`) |
| **MCA21 Corporate Portal** | `OFFICIAL_API` | `LiveMCAAdapter` | Configuration Required (`MCA_API_KEY`) |
| **EPFO Shram Suvidha** | `OFFICIAL_API` | `LiveEPFOAdapter` | Configuration Required (`EPFO_API_KEY`) |
| **ESIC Portal** | `MANUAL` / `AUTHORIZED` | `LiveEPFOAdapter` | Manual / Configuration Required |
| **DigiLocker Gateway** | `OFFICIAL_API` | `LiveDigiLockerAdapter` | Configuration Required (`DIGILOCKER_API_KEY`) |
| **Government e-Marketplace (GeM)** | `OFFICIAL_API` | `LiveGeMAdapter` | Authoritative Integration Required |
| **Debarment / Blacklisting** | `MANUAL` / `SYNTHETIC` | `DebarmentVerificationProvider` | Manual Officer Review / Synthetic |
| **Startup India / DPIIT** | `MANUAL` / `SYNTHETIC` | `StartupNSICVerificationProvider` | Manual Officer Review / Synthetic |
| **OEM Authorization** | `MANUAL` / `SYNTHETIC` | `OEMAuthorizationVerificationProvider` | Manual Officer Review / Synthetic |
| **Make in India / Local Content** | `MANUAL` / `SYNTHETIC` | `MakeInIndiaVerificationProvider` | Manual Officer Review / Synthetic |

---

## 3. Security & Safety Controls

1. **SSRF Protection**: Live HTTP adapters (`BaseLiveHttpAdapter`) strictly validate destination URLs against server-configured base URL variables. User-supplied target URLs are forbidden.
2. **Credential Protection**: Secrets, API keys, and auth headers are configured via environment variables (`.env`) and are **never** hardcoded, written to audit logs, or exposed in API responses.
3. **No Unsafe Fallback**: Missing credentials or upstream errors produce explicit `ERROR` or `PENDING` states with machine-readable reasons (`OFFICIAL_INTEGRATION_NOT_CONFIGURED`, `UPSTREAM_UNAVAILABLE`). The system **never** silently converts errors to `VERIFIED` or silently substitutes synthetic data in production mode.
4. **No Unauthorized Scraping**: The platform strictly complies with government portal Terms of Service and security controls. No CAPTCHA bypassing or unauthorized portal scraping is performed.

---

## 4. API & Audit Endpoints

- `GET /verification/providers`: Returns capability metadata and source modes for all registered connectors without exposing secrets.
- `POST /verification/manual`: Enables an authorized Procurement Officer or Admin to record a manual verification outcome with audit trail logging.
