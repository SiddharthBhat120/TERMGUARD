# TermGuard evaluation results

Engine: **rule engine (offline)**. Documents: 11. Clauses: 88. Findings shown: 48. Run time: 2.0s.

> These numbers come from the synthetic sample set in `samples/public/`, labelled clause by clause.
> The rules were written alongside these samples, so treat the scores as optimistic. Add your own
> redacted documents to `samples/private/`, label them with `eval/label_tool.py`, and rerun.

## Overall

| Metric | Value |
|---|---|
| Precision | 98% (47 of 48 findings were correct) |
| Recall | 89% (47 of 53 labelled risks were found) |
| F1 | 0.93 |
| Findings dropped by the quote check | 0 |
| Findings shown without a verified quote | 0 |
| Reading ease of explanations (Flesch, higher is easier) | 83.4 |

## Per checklist item

| Item | Name | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|---|
| `O01_variable_pay` | Large or uncertain variable pay | 2 | 0 | 0 | 100% | 100% |
| `O02_bond` | Service bond or training-cost recovery | 2 | 0 | 0 | 100% | 100% |
| `O03_long_notice` | Long notice period | 3 | 0 | 0 | 100% | 100% |
| `O04_buyout` | Notice buyout limits | 2 | 0 | 0 | 100% | 100% |
| `O05_probation` | Strict probation terms | 2 | 0 | 0 | 100% | 100% |
| `O06_non_compete` | Non-compete after you leave | 1 | 0 | 1 | 100% | 50% |
| `O07_ip_assignment` | Broad ownership of your work | 1 | 0 | 1 | 100% | 50% |
| `O08_relocation_clawback` | Joining or relocation bonus clawback | 1 | 0 | 1 | 100% | 50% |
| `O09_unilateral_change` | Company can change terms alone | 2 | 0 | 0 | 100% | 100% |
| `O10_offer_withdrawal` | Offer can be withdrawn | 1 | 0 | 0 | 100% | 100% |
| `O11_salary_confidential` | Salary must be kept secret | 1 | 0 | 0 | 100% | 100% |
| `O12_final_pay_deduction` | Deductions from your final settlement | 1 | 0 | 0 | 100% | 100% |
| `R01_deposit_high` | Large security deposit | 2 | 0 | 0 | 100% | 100% |
| `R02_deposit_forfeit` | Deposit can be kept or not refunded | 3 | 0 | 0 | 100% | 100% |
| `R03_vague_deductions` | Open-ended deductions from deposit | 1 | 0 | 0 | 100% | 100% |
| `R04_lock_in` | Lock-in period | 2 | 0 | 2 | 100% | 50% |
| `R05_long_notice` | Long notice period for you | 4 | 0 | 0 | 100% | 100% |
| `R06_eviction` | Eviction without fair notice | 3 | 0 | 0 | 100% | 100% |
| `R07_rent_increase` | Rent increase terms | 3 | 0 | 1 | 100% | 75% |
| `R08_repairs_on_tenant` | All repairs put on you | 3 | 0 | 0 | 100% | 100% |
| `R09_usage_restrictions` | Limits on visitors or daily life | 2 | 1 | 0 | 67% | 100% |
| `R10_exit_charges` | Painting or exit charges | 2 | 0 | 0 | 100% | 100% |
| `R11_entry_without_notice` | Owner can enter without notice | 1 | 0 | 0 | 100% | 100% |
| `R12_late_fee` | Late payment penalty | 2 | 0 | 0 | 100% | 100% |

## Failure cases

- Missed `O07_ip_assignment` in `offer_fair_product_company.pdf` / Intellectual property
- Missed `O06_non_compete` in `offer_internship_ppo.pdf` / Exit Restrictions
- Missed `O08_relocation_clawback` in `offer_sales_variable_heavy.pdf` / Joining bonus
- Missed `R04_lock_in` in `rental_pg_hostel_rules.pdf` / Advance
- Missed `R07_rent_increase` in `rental_pg_hostel_rules.pdf` / Fee Revision
- Missed `R04_lock_in` in `rental_scanned_copy.pdf` / Deposit
- False alarm `R09_usage_restrictions` in `rental_scanned_copy.pdf` / Pets: "No pets are allowed in the premises"

## Why recall matters more here

Missing a risky clause costs the user far more than reading one extra explanation, so the
checklist patterns lean towards recall. Precision is protected differently: every finding
must quote the document, so a false alarm is visible and easy to dismiss.
