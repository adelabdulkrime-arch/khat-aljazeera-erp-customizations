# Khat Al Jazeera Auto Maintenance — ERP System Audit

**Prepared for:** Khat Al Jazeera Auto Maintenance
**Subject system:** ERPNext v16 + custom `khat_workshop` app (vendor: One Media)
**Audit date:** 2026-07-22
**Method:** Direct inspection of the running production instance (database, container images, deployment pipeline, application source) — not a questionnaire-based review.

> **Evidence rating used throughout**
> **[V]** Verified directly against the running system.
> **[C]** Confirmed absent by inspection.
> **[?]** Not verified — must be answered by One Media.

---

## 0. Executive Summary

The system is **technically sound but functionally incomplete for a multi-discipline body shop.**

The accounting foundation is genuinely correct: a live end-to-end transaction test posted 5% Oman VAT accurately, produced balanced GL entries (Dr 210 = Cr 210), and settled to zero outstanding. Infrastructure is stable, backups are automated and *restore-tested*.

However, the operational core — the **Work Card** — is modelled as a **document, not a process.** It records *what was agreed*; it does not control *what happened*. The five gaps below are not refinements. Each is a direct revenue-leakage or liability exposure.

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | **Work Card is not submittable** — no `docstatus`. A closed job card can be edited by anyone, forever, with no lock. | 🔴 Critical | [V] |
| 2 | **No service-line segmentation.** No field distinguishes Mechanical / Body / Paint / Electrical / A-C. Departmental P&L is impossible. | 🔴 Critical | [C] |
| 3 | **No labour time capture.** Technician rows hold `task` + `commission` only — no clock-in/out, no hours. True job cost cannot be computed. | 🔴 Critical | [V] |
| 4 | **No insurance claim structure.** No insurer, policy, claim ref, deductible, or approval state — despite Accident Restoration being a core service line. | 🔴 Critical | [C] |
| 5 | **No vehicle intake condition record.** No fuel level, damage map, photos, or accessories checklist — the primary defence against customer damage disputes in a body shop. | 🔴 Critical | [C] |

**Verdict:** Do not treat this as "finished and needing polish." Treat it as a **solid financial platform with an incomplete workshop layer.** The remediation is well-bounded and mostly additive.

---

## 1. End-to-End Operational Workflow & Process Mapping

### 1.1 Current vs. required state

| Stage | Required | System today | Gap |
|---|---|---|---|
| **Gate Entry** | Odometer, fuel level, damage map, photos, accessories checklist, customer signature | Odometer (`mileage`) and entry date only **[V]** | 🔴 No condition evidence |
| **Job Card & Estimate** | Estimate → approval → firm order, estimate vs. actual variance | Single `grand_total`; no separate estimate **[V]** | 🟠 No variance control |
| **Customer Approval** | Recorded approval, timestamp, channel, signature | None **[C]** | 🔴 No consent trail |
| **Insurance Approval** | Insurer, claim, survey, deductible, approved lines | None **[C]** | 🔴 Blocks a core service line |
| **Task Assignment & Labour** | Assign, clock in/out, actual hours, efficiency | Technician + free-text `task` + manual `commission` **[V]** | 🔴 No time, no true cost |
| **Parts Requisition** | Reserve → issue → return unused, per job | Auto Stock Entry (Material Issue) on status "جاهزة للتسليم" **[V]** | 🟠 One-shot; no return |
| **Paint & Consumables** | Mixed volume, colour code, panel count, wastage | None **[C]** | 🔴 Paint cost invisible |
| **Quality Control** | Checklist, inspector, pass/fail, rework loop | None **[C]** | 🔴 No rework capture |
| **Closure & Invoice** | Lock card → invoice → payment → gate pass | Native Sales Invoice + Payment Entry **[V]** | 🟠 No lock, no gate pass |

### 1.2 The critical control break

Parts are issued to stock **on status change alone** — a plain Link field with **no workflow transitions** [V]. Consequences:

- Any user can set "جاهزة للتسليم" and trigger a real, submitted, irreversible `Stock Entry`.
- Reverting the status does **not** reverse the stock movement.
- There is no approval gate between estimate and material consumption.

**This is the single highest-risk mechanism in the system.**

### 1.3 Required Work Card state machine

```
Draft → Awaiting Inspection → Estimated → Awaiting Customer/Insurer Approval
      → Approved → In Progress → Awaiting Parts → QC → Rework (loop to In Progress)
      → Ready for Delivery → Invoiced → Delivered → Closed [LOCKED]
```

Rules to enforce: no parts issue before **Approved**; no invoice before **QC Passed**; no edits after **Closed** except by a reversing document.

---

## 2. Architecture, UI/UX & Redundancy Analysis

### 2.1 Architectural health — materially improved

| Area | Status |
|---|---|
| Custom code isolation | ✅ Real Frappe app; **zero** framework pollution **[V]** |
| Duplicate/shadow documents | ✅ Retired; native Quotation / Sales Invoice / Payment Entry **[V]** |
| Image consistency | ✅ All 9 services on one image **[V]** |
| Backups | ✅ Automated, separate volume, **restore-tested** (913 tables) **[V]** |
| Off-site backups | 🔴 **Absent** — backups share the server they protect **[C]** |

### 2.2 UX evaluation checklist (workshop-floor reality)

**Technician (gloved hands, tablet, poor lighting)**
- [ ] Clock in/out in ≤ 2 taps — *no mechanism exists today* **[C]**
- [ ] Photo capture from device camera directly onto the job card **[C]**
- [ ] Large touch targets; no free-text where a picklist works
- [ ] Offline tolerance in the workshop bay **[?]**

**Service Advisor (customer waiting at counter)**
- [ ] Vehicle lookup by plate in one field — *plate exists but is `Data`, denormalised from Customer Vehicle* **[V]**
- [ ] Full history for the vehicle on one screen **[?]**
- [ ] Estimate → approval → print/send without leaving the record **[C]**

### 2.3 Redundancy & data-integrity issues found

| Issue | Detail | Recommendation |
|---|---|---|
| **Denormalised fields** | `customer_phone`, `plate_number`, `brand`, `model` are copied onto Work Card while also living on Customer / Customer Vehicle **[V]** | Make them fetched read-only, not stored duplicates — they will drift |
| **Free-text services** | `Work Card Service.service` is `Data`, not a Link **[V]** | Convert to a **Service Item** master — otherwise no standard pricing, no service analytics, no labour rates |
| **Manual commission** | Entered per row despite `commission_rate` existing on Workshop Technician **[V]** | Auto-calculate; manual entry invites both error and manipulation |
| **Single service item** | All invoicing historically funnelled through `WORKSHOP-SERVICE` **[V]** | Use real service items per discipline |

### 2.4 Gap analysis — modern expectations

| Feature | Status | Business impact |
|---|---|---|
| WhatsApp/SMS status updates | 🟠 Invoice-send script exists; **no status automation** **[V]** | High inbound call volume |
| Customer tracking portal | 🔴 Absent **[C]** | Advisor time lost to status calls |
| Warranty management | 🔴 Absent **[C]** | Cannot distinguish paid vs. warranty rework |
| Returns (parts & sales) | 🟠 ERPNext native exists; **not wired to Work Card** **[V]** | Unused parts silently become losses |
| Appointment / bay scheduling | 🔴 Absent **[C]** | No capacity planning |
| Vehicle service history | 🟠 Data exists; no consolidated view **[?]** | Weak upsell, weak diagnostics |
| Digital inspection (DVI) | 🔴 Absent **[C]** | Lost upsell; no dispute evidence |

---

## 3. Financial & Accounting Architecture Audit

### 3.1 Verified strengths

Live transaction test — **12/12 assertions passed** [V]:

| Assertion | Result |
|---|---|
| Oman VAT 5% applied | ✅ Exactly 10.000 on net 200 |
| Currency | ✅ OMR (3 decimals, Baisa) |
| GL entries posted | ✅ 3 entries |
| **Double-entry balanced** | ✅ Dr 210.000 = Cr 210.000 |
| Payment settles invoice | ✅ Outstanding → 0 |

Because the system now posts through **native ERPNext documents**, it inherits a genuinely IFRS-compatible engine: accrual basis, double-entry integrity, perpetual inventory, and immutable submitted documents.

> **Historic risk, now closed:** the retired bridge generated Sales Invoices with **no tax rows at all** — invoices posted at 0% VAT. This was a tax-compliance exposure, not a cosmetic bug. It is fixed and verified.

### 3.2 Required automated journal entries

**A. Purchase & receive parts/paint**
| | Account | Dr | Cr |
|---|---|---|---|
| Receipt | Stock In Hand — Parts | X | |
| | Stock Received But Not Billed | | X |
| Invoice | Stock Received But Not Billed | X | |
| | VAT Input (Recoverable) | Y | |
| | Accounts Payable — Supplier | | X+Y |

**B. Issue parts to a Job Card — job costing** *(currently posts to generic expense, not per-job)* 🔴
| Account | Dr | Cr |
|---|---|---|
| WIP — Job #____ | X | |
| Stock In Hand — Parts | | X |

**C. Labour & commission** 🔴 *not implemented*
| Account | Dr | Cr |
|---|---|---|
| WIP — Job #____ (labour absorbed) | X | |
| Labour Absorption / Payroll Accrual | | X |
| Technician Commission Expense | C | |
| Commission Payable | | C |

**D. Invoice & revenue recognition**
| Account | Dr | Cr |
|---|---|---|
| AR / Cash / Insurance Receivable | G | |
| Revenue — *by service line* | | N |
| VAT Output Payable | | T |
| COGS — Job | W | |
| WIP — Job | | W |

> **Gap:** revenue is not segmented by service line, and **no WIP account is used at all** — parts hit expense immediately. This breaks job-level gross margin.

**E. Insurance claims** 🔴 *not implemented* — requires split between customer deductible and insurer receivable, with separate ageing.

### 3.3 Financial stress test cases

| # | Test | Detects | Expected |
|---|---|---|---|
| F1 | Issue parts, then revert Work Card status | Phantom stock | Stock reversed or transition blocked |
| F2 | Close job card, then edit totals | Post-closure tampering | Blocked — **currently NOT blocked** 🔴 |
| F3 | Invoice with 100% discount | Revenue leakage | Requires approval; VAT recalculated |
| F4 | Part issued but never invoiced | Leakage | Exception report flags unbilled WIP |
| F5 | Cancel invoice after payment | Orphan cash | Payment unallocated, not deleted |
| F6 | Insurance pays less than invoiced | Write-off control | Variance to approved write-off account |
| F7 | Two users invoice one job card | Duplicate revenue | Second attempt blocked |
| F8 | Backdate invoice to closed period | Period integrity | Blocked by period-closing voucher **[?]** |
| F9 | Negative stock issue | Valuation corruption | Blocked |
| F10 | Change item valuation retroactively | COGS distortion | Repost + audit trail |

---

## 4. Inventory & Supply Chain

| Capability | Status | Note |
|---|---|---|
| Non-serialised parts | ✅ Native **[V]** | Work Card Part links a real Item |
| **Serialised parts** | 🟠 Native support exists; **not enforced** in workshop flow **[?]** | Batteries, ECUs, tyres need serials |
| **Batch/expiry** | 🟠 Native; not wired **[?]** | Paint, oils, chemicals have shelf life |
| **Bulk consumables / paint mixing** | 🔴 **Absent** **[C]** | No UOM conversion litre→ml, no mix formula, no wastage |
| Reorder alerts | 🟠 Native; configuration unverified **[?]** | |
| Valuation (FIFO / Moving Average) | 🟠 Native; **policy not set per item group** **[?]** | Must be a deliberate, documented choice |
| Purchase returns | 🟠 Native; not wired to workshop | |
| **Unused-parts return to store** | 🔴 **Absent** **[C]** | Over-issued parts stay charged to the job |

**Paint is the largest blind spot.** For a shop doing body + refinishing, paint and consumables are a major cost pool with zero system representation today.

---

## 5. Security, RBAC & Audit Logs

### 5.1 Current state

Roles created: `Workshop Manager`, `محاسب`, `مدير المستودع`, `مسؤول المشتريات`, `مندوب مبيعات`, `كاشير` **[V]** — but they are **containers with no permission matrix designed around segregation of duties** [?]. Only 3 users exist; the system has not yet met real users.

### 5.2 Proposed RBAC matrix

| Function | Advisor | Technician | Store | Accountant | Manager |
|---|---|---|---|---|---|
| Create Work Card | ✅ | — | — | — | ✅ |
| Edit estimate | ✅ | — | — | — | ✅ |
| **Approve estimate** | — | — | — | — | ✅ |
| Clock labour | — | ✅ (own) | — | — | ✅ |
| Issue parts | — | Request | ✅ | — | ✅ |
| **QC pass** | — | — | — | — | ✅ (QC role) |
| Create invoice | ✅ | — | — | ✅ | ✅ |
| **Apply discount > threshold** | — | — | — | — | ✅ |
| Receive payment | ✅ | — | — | ✅ | ✅ |
| **Cancel/amend submitted doc** | — | — | — | — | ✅ + reason |
| **Edit closed Work Card** | ❌ | ❌ | ❌ | ❌ | ❌ |
| Change item valuation | — | — | — | ✅ | ✅ |
| Manage users/roles | — | — | — | — | ✅ (Admin only) |

**Segregation of duties:** whoever approves a discount must not also receive the cash. Whoever issues parts must not also close the job card.

### 5.3 Data integrity & audit requirements

- [ ] **Submittable + locked Work Card** — highest priority 🔴
- [ ] Immutable audit log on: discount, status transition, parts issue, invoice cancel, payment edit
- [ ] `track_changes` enabled on all financial doctypes **[?]**
- [ ] Period-closing voucher to prevent backdating **[?]**
- [ ] **Off-site encrypted backups** — currently backups sit on the machine they protect 🔴 **[C]**
- [ ] Documented restore drill — *one has been performed and passed* ✅ **[V]**
- [ ] MFA for Manager/Accountant **[?]**
- [ ] PII handling policy for customer phone/vehicle data **[?]**

---

## 6. Technical Interrogation Questionnaire — for One Media

### A. Workflow & control
1. Why is Work Card **not submittable**? How is a closed job card protected from edits today?
2. What prevents a user from triggering a real stock issue by changing a status field?
3. Where is technician labour time recorded, and how is job labour cost derived without it?
4. How do you report **profit per service line** (Mechanical / Body / Paint / Electrical / A-C) with no department field?
5. Where is the QC step, and how is rework distinguished from new work?

### B. Insurance & body shop
6. How is an insurance job handled end-to-end — insurer, claim, survey, deductible, partial approval?
7. How is customer deductible split from insurer receivable in AR?
8. How is paint consumption costed — mixing, colour code, wastage?
9. Where is the intake condition record (photos, damage map, fuel, accessories)?

### C. Financial
10. Is a **WIP account** used for job costing, or do parts hit expense on issue?
11. What is the inventory valuation policy per item group, and who approved it?
12. How is a discount above threshold authorised and logged?
13. What happens accounting-wise when an invoice is cancelled after payment?
14. Is period closing enforced against backdated entries?

### D. Data & operations
15. What is the **off-site** backup strategy and RPO/RTO commitment?
16. When was a restore last tested, by whom, with what result?
17. Which fields are denormalised, and what keeps them in sync?
18. What is the upgrade path for ERPNext/hrms, and how are customisations re-tested?
19. Is there an automated regression test suite? *(A 12-assertion accounting smoke test now exists — is it in CI?)*
20. What is the RBAC matrix as designed, and has segregation of duties been reviewed?

---

## 7. Prioritised Remediation Roadmap

| Phase | Items | Why first |
|---|---|---|
| **P0 — Control** | Make Work Card submittable + locked; Work Card **Workflow** with transition rules; gate parts issue behind Approved | Stops tampering and phantom stock |
| **P1 — Revenue integrity** | Service-line field + segmented revenue accounts; Service Item master; WIP job costing | Enables departmental P&L |
| **P2 — Core operations** | Labour time capture; QC step + rework loop; intake condition record with photos | Closes cost and liability gaps |
| **P3 — Insurance & paint** | Insurance claim structure; paint/consumable costing with UOM conversion | Unlocks two core service lines |
| **P4 — Customer experience** | WhatsApp status automation; tracking portal; warranty; parts return | Competitive parity |
| **P5 — Assurance** | Off-site backups; RBAC hardening; audit log rules; CI regression | Operational resilience |

---

## 8. Closing Assessment

**Do not rebuild.** The foundation is correct and the hardest architectural problems have already been solved: the code is a proper app, the shadow bookkeeping is gone, VAT posts accurately, and the double-entry engine is native ERPNext behaving correctly under test.

What remains is **workshop domain depth** — and the single most urgent item is not a feature at all. It is a control: **a Work Card that cannot be locked is a Work Card that cannot be trusted**, and every financial figure downstream inherits that weakness.

Fix P0 before the system carries real customer money.

---

*Findings marked **[V]** and **[C]** were verified by direct inspection of the running production instance. Items marked **[?]** require confirmation from One Media and are deliberately framed as questions rather than assertions.*
