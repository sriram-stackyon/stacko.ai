# FUTURE_VISION.md — Long-Term Product Roadmap
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> This document describes what a production-grade version of this system would look like **after** the 2-week capstone. Nothing in this document is in scope for the demo.

---

## Section 0 — In-Scope: What Was Built in 2 Weeks

| Feature | Evidence |
|---|---|
| Claim submission form (policy number, incident type, description, photos) | `ClaimForm.jsx` — multipart form upload |
| Policy verification against Supabase mock policies table | `policy_verification.py` — queries `policies` table |
| Damage assessment via GPT-4o vision | `damage_assessment.py` — passes photo URLs as image_url content parts |
| Fraud detection via GPT-4o text + claim history | `fraud_detection.py` — queries prior claims, calls LLM |
| Claims adjudication (approved/denied/escalated) with business rules | `adjudication.py` — 5-step rule engine + LLM fallback |
| Customer email draft generation | `communication.py` — professional email via GPT-4o |
| Claims result UI with decision badge and payout | `ClaimResult.jsx` — coloured badges, damage summary |
| Claims history UI with clickable rows | `ClaimsHistory.jsx` — table with all past claims |
| Supabase persistence (claims + photo storage) | `claims.py` route + Supabase Storage bucket |

---

## Phase 2 — Production Hardening (Months 1–3)

### Real Policy Database Integration
Replace the mock `policies` table with a live connection to an insurer's policy management system via REST API or secure database tunnel. Add real-time policy status checks (e.g., mid-term cancellations, endorsements).

### Actual Email/SMS Delivery
Integrate SendGrid (email) and Twilio (SMS) to send the generated customer communication automatically. Add delivery tracking and retry logic.

### Claimant Authentication
Add Auth0 or Supabase Auth for claimant identity verification. Each claimant can only see their own claims. Adjusters get a separate admin role with full access.

### Adjuster Dashboard
Build a dedicated UI for human adjusters to review `escalated` claims. Adjusters can override the AI decision, add notes, and trigger the email send manually.

### Document Upload Support
Extend the file upload to accept PDFs (police reports, medical bills, repair quotes) alongside photos. Use GPT-4o vision to extract key figures from scanned documents.

---

## Phase 3 — Intelligent Fraud Detection (Months 4–6)

### Dedicated ML Fraud Model
Train a classification model (LightGBM or XGBoost) on historical claims data with known fraud labels. Use the LLM fraud node as a pre-screening filter; the ML model handles final risk scoring.

### Graph-Based Fraud Network Analysis
Detect fraud rings by building a graph of claimants, policies, repair shops, and witnesses. Flag when the same third-party entities appear across multiple unrelated claims.

### Automated SIU Escalation
When the fraud model score exceeds a threshold, automatically open a case in the Special Investigations Unit (SIU) system and assign it to an investigator.

---

## Phase 4 — Multi-Line Insurance Support (Months 7–12)

### Product Lines
Extend beyond auto insurance to support:
- **Property / Home Insurance**: Structural damage assessment using drone/satellite imagery
- **Health Insurance**: Medical bill review against policy coverage schedules
- **Life Insurance**: Beneficiary verification and cause-of-death documentation review

### Multi-Language Support
Generate customer communications in the claimant's preferred language using GPT-4o's multilingual capability. Store language preference per claimant profile.

### Mobile App
Native iOS/Android app for claimants to submit claims, upload photos directly from their camera, and track claim status in real time via push notifications.

---

## Phase 5 — Regulatory Compliance & Auditability (Year 2)

### Full Audit Trail
Every LLM call is logged with inputs, outputs, token counts, and latency. Adjusters and regulators can view the complete reasoning trace for any claim decision.

### Explainable AI Reports
Generate a PDF report for each claim showing exactly what signals drove the adjudication decision, formatted for regulatory disclosure (e.g., to comply with adverse action notice requirements).

### Bias Monitoring
Continuously monitor decision rates by demographic group (using proxy variables like zip code) to detect and correct disparate impact in the fraud detection model.

### SOC 2 Type II Compliance
Implement access controls, encryption at rest, audit logging, and incident response procedures required for insurance industry certification.

---

## Architecture Evolution

```
2-Week Demo:
  React → FastAPI → LangGraph (sequential, 6 nodes) → GPT-4o → Supabase

Phase 2 (Production):
  React → FastAPI → LangGraph (conditional routing) → GPT-4o / Fine-tuned models
                 ↓                                          ↓
           Redis Queue                              ML Fraud Model (Sagemaker)
                 ↓
           Worker Process → Policy API → Claims DB (PostgreSQL) → S3 Photo Storage

Phase 3+ (Enterprise):
  Mobile App → API Gateway → Microservices (Claims, Fraud, Communication)
                                    ↓
                           Event Streaming (Kafka)
                                    ↓
                           Data Warehouse → BI Dashboard → Regulatory Reports
```
