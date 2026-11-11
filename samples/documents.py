"""Synthetic sample documents for demos, tests and evaluation.

Every name, address, phone number and amount here is made up. No real documents are
stored in this repository.

Each clause carries `labels`: the checklist items a careful human reviewer would flag in
it. These labels were written from the meaning of the clause, not from TermGuard's
patterns, so the evaluation can find real misses.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class C:
    heading: str
    text: str
    labels: list[str] = field(default_factory=list)


@dataclass
class Doc:
    name: str
    kind: str  # rental | offer_letter
    style: str  # numbered | clause | caps | plain | letter
    title: str
    intro: list[str]
    clauses: list[C]
    outro: list[str] = field(default_factory=list)
    scanned: bool = False


DOCS: list[Doc] = [
    Doc(
        name="rental_bengaluru_strict", kind="rental", style="numbered",
        title="RENTAL AGREEMENT",
        intro=[
            "This Rental Agreement is made at Bengaluru on 1st June 2026 between Mr. Ramesh Kulkarni, "
            "S/o Shri Venkatesh Kulkarni, residing at #42, 3rd Cross, Jayanagar 4th Block, Bengaluru 560011 "
            "(hereinafter called the OWNER) and Mr. Arjun Menon, residing at Flat No. 12B, Lake View "
            "Apartments, Kakkanad, Kochi 682030 (hereinafter called the TENANT). Phone: 98450 12345.",
        ],
        clauses=[
            C("Premises", "The Owner agrees to let out the residential flat at No. 7, 2nd Floor, Sri Sai Residency, "
              "BTM Layout, Bengaluru 560076, along with the fittings listed in the Schedule below."),
            C("Period", "The tenancy shall be for a period of 11 (eleven) months commencing from 1st June 2026."),
            C("Rent", "The Tenant shall pay a monthly rent of Rs. 18,000/- (Rupees Eighteen Thousand only) on or "
              "before the 5th day of every English calendar month."),
            C("Security Deposit", "The Tenant has paid a sum of Rs. 1,80,000/- being ten months' rent as security "
              "deposit, which shall carry no interest. The Owner may forfeit the deposit at his sole discretion "
              "in case of any breach by the Tenant.", ["R01_deposit_high", "R02_deposit_forfeit"]),
            C("Deductions", "At the time of vacating, the Owner shall be entitled to deduct any amount he deems fit "
              "towards damages, dues and other charges from the security deposit.", ["R03_vague_deductions"]),
            C("Lock-in", "There shall be a lock-in period of 11 months. If the Tenant vacates before the expiry of "
              "the lock-in period, he shall pay rent for the remaining unexpired period.", ["R04_lock_in"]),
            C("Notice", "The Tenant shall give three months' written notice before vacating the premises. The Owner "
              "may terminate this agreement at any time without assigning any reason.",
              ["R05_long_notice", "R06_eviction"]),
            C("Maintenance", "All repairs of whatever nature, including plumbing and electrical, shall be carried out "
              "by the Tenant at his own cost.", ["R08_repairs_on_tenant"]),
            C("Painting", "One month's rent shall be deducted towards painting charges when the Tenant vacates the "
              "premises, irrespective of the condition of the walls.", ["R10_exit_charges"]),
            C("Inspection", "The Owner or his agents shall have the right to enter and inspect the premises at any "
              "time.", ["R11_entry_without_notice"]),
            C("Use", "The premises shall be used for residential purposes only. No visitors shall be allowed after "
              "9 PM.", ["R09_usage_restrictions"]),
        ],
        outro=["Schedule: 2 fans, 4 tube lights, 1 geyser, kitchen cabinets.",
               "Signed by the Owner and the Tenant in the presence of two witnesses."],
    ),
    Doc(
        name="rental_mumbai_leave_licence", kind="rental", style="clause",
        title="LEAVE AND LICENCE AGREEMENT",
        intro=[
            "This agreement is made on 15 July 2026 between Smt. Kavita Deshpande (the LICENSOR) and "
            "Ms. Priya Nair (the LICENSEE), email priya.nair@example.com.",
        ],
        clauses=[
            C("Grant of licence", "The Licensor grants the Licensee a licence to use Flat No. 304, Shanti Kunj, "
              "Andheri East, Mumbai 400069 for residential use only."),
            C("Licence fee", "The licence fee shall be Rs. 32,000 per month, payable in advance by the 7th of each "
              "month by bank transfer. The licence fee shall be increased by 10% every eleven months.",
              ["R07_rent_increase"]),
            C("Deposit", "The Licensee shall pay an interest-free refundable deposit of Rs. 1,50,000. The deposit "
              "shall be refunded within 30 days of the Licensee handing over vacant possession, after deducting "
              "unpaid licence fee and bills."),
            C("Duration and lock-in", "This licence is for 11 months. Neither party shall terminate the licence "
              "during the first six months.", ["R04_lock_in"]),
            C("Termination", "After the first six months, either party may terminate this licence by giving one "
              "month's prior written notice."),
            C("Late payment", "If the licence fee is not paid by the due date, a penalty of Rs. 200 per day shall "
              "be payable until payment is made.", ["R12_late_fee"]),
            C("Society charges", "The Licensor shall pay the society maintenance charges and property tax. The "
              "Licensee shall pay electricity and gas bills as per actual consumption."),
            C("Repairs", "Minor day-to-day repairs shall be done by the Licensee. Major and structural repairs "
              "shall be the responsibility of the Licensor."),
            C("Registration", "This agreement shall be registered with the Sub-Registrar and the stamp duty and "
              "registration charges shall be shared equally by both parties."),
        ],
        outro=["Signed at Mumbai."],
    ),
    Doc(
        name="rental_fair_model", kind="rental", style="numbered",
        title="TENANCY AGREEMENT",
        intro=["This Tenancy Agreement is entered into on 1 August 2026 between the Landlord, Mr. Suresh Rao, "
               "and the Tenant, Mr. Kiran Shetty, for the premises at Kadri, Mangaluru 575002."],
        clauses=[
            C("Term", "The tenancy is for a period of twelve months starting 1 August 2026, renewable by mutual "
              "written consent."),
            C("Rent", "The monthly rent is Rs. 12,000, payable on or before the 10th of each month. The Landlord "
              "shall issue a receipt for every payment."),
            C("Security deposit", "The Tenant shall pay a security deposit of Rs. 24,000, equal to two months' rent. "
              "The deposit shall be returned within 30 days of the Tenant vacating, after deducting only unpaid "
              "rent, unpaid bills and the cost of damage beyond normal wear and tear, supported by bills."),
            C("Rent revision", "The rent may be revised once every twelve months by not more than 5% with two "
              "months' written notice to the Tenant.", ["R07_rent_increase"]),
            C("Repairs", "The Landlord shall carry out structural repairs, whitewashing of walls and repairs to "
              "plumbing and wiring. The Tenant shall carry out minor repairs caused by daily use."),
            C("Entry", "The Landlord may enter the premises for inspection or repairs after giving at least 24 hours' "
              "prior written notice, except in an emergency."),
            C("Notice", "Either party may end this agreement by giving one month's written notice."),
            C("Inventory", "A list of fittings and their condition, signed by both parties, is attached as Annexure A."),
            C("Registration", "This agreement shall be executed on e-stamp paper and registered as required by law."),
        ],
    ),
    Doc(
        name="rental_pg_hostel_rules", kind="rental", style="caps",
        title="PAYING GUEST ACCOMMODATION AGREEMENT",
        intro=["Agreement between Sri Lakshmi Ladies PG (the OWNER) and the Resident, Ms. Ananya Gupta, "
               "phone 91234 56789, for a twin-sharing room in Koramangala, Bengaluru."],
        clauses=[
            C("CHARGES", "The Resident shall pay Rs. 14,500 per month towards rent and food on or before the 1st "
              "of every month."),
            C("ADVANCE", "An advance of Rs. 29,000 has been collected. The advance is non-refundable if the Resident "
              "leaves without completing six months.", ["R02_deposit_forfeit", "R04_lock_in"]),
            C("HOUSE RULES", "Guests and visitors are not permitted inside the rooms. Residents must return by 10 PM. "
              "Cooking and non-veg food are not allowed in the rooms. Violation will attract a fine of Rs. 1,000.",
              ["R09_usage_restrictions"]),
            C("VACATING", "The Resident must inform the Owner 60 days in advance before vacating. Cleaning charges of "
              "Rs. 2,500 will be collected at the time of vacating.", ["R05_long_notice", "R10_exit_charges"]),
            C("TERMINATION", "The Owner may ask the Resident to vacate immediately in case of any misbehaviour, "
              "as decided by the Owner.", ["R06_eviction"]),
            C("FEE REVISION", "The Owner may revise the monthly charges from time to time as per market conditions.",
              ["R07_rent_increase"]),
        ],
    ),
    Doc(
        name="rental_plain_letter_style", kind="rental", style="plain",
        title="Agreement to Let",
        intro=[],
        clauses=[
            C("", "This agreement is made between Mrs. Lata Iyer, the owner of the house at Gandhi Nagar, Udupi, and "
              "Mr. Rohan Das, the tenant, on 5 September 2026."),
            C("", "The tenant will pay a monthly rent of Rs. 9,500 by the 5th of every month and an advance of "
              "Rs. 50,000 which will be returned when the tenant vacates."),
            C("", "The owner can increase the rent whenever he wants after informing the tenant.",
              ["R07_rent_increase"]),
            C("", "The tenant must look after all maintenance of the house, including the roof and water tank, at his "
              "own expense.", ["R08_repairs_on_tenant"]),
            C("", "If the tenant wishes to leave, he must give two months notice. If rent is delayed, interest at "
              "24% per annum will be charged.", ["R05_long_notice", "R12_late_fee"]),
            C("", "The owner may disconnect the water and electricity supply if rent is not paid on time.",
              ["R06_eviction"]),
        ],
    ),
    Doc(
        name="rental_scanned_copy", kind="rental", style="numbered", scanned=True,
        title="RENT AGREEMENT",
        intro=["This Rent Agreement is made on 10 October 2026 at Mysuru between Mr. Prakash Hegde (Landlord) and "
               "Mr. Nikhil Joshi (Tenant)."],
        clauses=[
            C("Rent", "The Tenant shall pay a monthly rent of Rs. 11,000 on or before the 5th day of each month."),
            C("Deposit", "The Tenant shall pay a security deposit equal to six months rent. The deposit shall not be "
              "refunded if the Tenant leaves before 11 months.", ["R01_deposit_high", "R02_deposit_forfeit", "R04_lock_in"]),
            C("Notice", "The Tenant shall give three months prior notice before vacating the house.",
              ["R05_long_notice"]),
            C("Repairs", "The Tenant shall bear the cost of all repairs to the house.", ["R08_repairs_on_tenant"]),
            C("Pets", "No pets are allowed in the premises."),
        ],
    ),
    # --------------------------- Offer letters ---------------------------
    Doc(
        name="offer_startup_bond", kind="offer_letter", style="letter",
        title="OFFER OF EMPLOYMENT",
        intro=["Brightloop Technologies Pvt. Ltd., 3rd Floor, Embassy Tech Square, Bengaluru 560103",
               "Date: 20 October 2026",
               "Dear Mr. Siddharth Rao,",
               "We are pleased to offer you the position of Associate Software Engineer on the following terms."],
        clauses=[
            C("Compensation", "Your total Cost to Company (CTC) will be Rs. 6,00,000 per annum. This includes a fixed "
              "pay of Rs. 4,20,000 per annum and a variable pay of Rs. 1,80,000 per annum, which is subject to "
              "company and individual performance and is paid at the sole discretion of the management.",
              ["O01_variable_pay"]),
            C("Date of joining", "Your date of joining will be 1 December 2026 at our Bengaluru office."),
            C("Service bond", "You will be required to serve the company for a minimum period of 24 months. If you "
              "leave before completing this period, you shall pay Rs. 2,00,000 towards training and recruitment "
              "costs.", ["O02_bond"]),
            C("Probation", "You will be on probation for six months, which may be extended at the discretion of the "
              "management. During probation, your services may be terminated without any notice.",
              ["O05_probation"]),
            C("Notice period", "After confirmation, either party may terminate employment by giving 90 days' notice. "
              "Buyout of the notice period is not permitted.", ["O03_long_notice", "O04_buyout"]),
            C("Leave", "You will be entitled to 18 days of paid leave and 10 public holidays per year."),
            C("Confidentiality", "Your salary details are strictly confidential and must not be shared with "
              "colleagues.", ["O11_salary_confidential"]),
        ],
        outro=["We look forward to working with you.", "For Brightloop Technologies Pvt. Ltd.",
               "HR Manager, hr@brightloop.example"],
    ),
    Doc(
        name="offer_it_services_training", kind="offer_letter", style="letter",
        title="LETTER OF OFFER",
        intro=["Nimbus Global Services Ltd., Pune",
               "Dear Ms. Sneha Kulkarni,",
               "With reference to your interview, we are happy to offer you employment as a Trainee Engineer."],
        clauses=[
            C("Salary", "Your annual CTC will be Rs. 3,60,000. The detailed salary breakup is given in Annexure 1."),
            C("Training", "You will undergo a training programme of 12 weeks. You will be required to sign a service "
              "agreement to work with the company for 18 months after training. If you leave earlier, the training "
              "cost of Rs. 1,50,000 shall be recovered from you.", ["O02_bond"]),
            C("Location", "You may be transferred to any location or project in India or abroad as per business "
              "needs.", ["O09_unilateral_change"]),
            C("Relocation", "A relocation allowance of Rs. 25,000 will be paid on joining. If you leave within 12 "
              "months, the full relocation allowance must be repaid.", ["O08_relocation_clawback"]),
            C("Notice", "You will be required to give two months' notice or pay salary in lieu of notice.",
              ["O03_long_notice", "O04_buyout"]),
            C("Verification", "This offer is subject to satisfactory background verification. If the verification "
              "is not satisfactory, this offer may be withdrawn at any time.", ["O10_offer_withdrawal"]),
            C("Working hours", "The working hours are 9:00 AM to 6:00 PM, Monday to Friday, at our Hinjewadi office."),
        ],
        outro=["Please sign and return a copy of this letter.", "Yours sincerely, Talent Acquisition Team"],
    ),
    Doc(
        name="offer_fair_product_company", kind="offer_letter", style="letter",
        title="Offer Letter",
        intro=["Lumen Labs India Pvt. Ltd., Kochi", "Dear Mr. Aditya Pai,",
               "We are delighted to offer you the role of Software Developer."],
        clauses=[
            C("Compensation", "Your annual CTC is Rs. 8,40,000, made up of a fixed salary of Rs. 8,00,000 and "
              "employer PF contribution. The full breakup is attached as Annexure A."),
            C("Joining", "Your joining date is 4 January 2027. You will work from our Infopark office, with two "
              "remote days each week."),
            C("Probation", "You will be on probation for three months. During probation, either side may end "
              "employment with 15 days' notice."),
            C("Notice period", "After probation, the notice period is 30 days for either side, and unused earned "
              "leave may be adjusted against it."),
            C("Leave", "You will receive 24 days of paid leave per year in addition to public holidays."),
            C("Intellectual property", "Work you create in the course of your employment and using company "
              "resources will belong to the Company. Personal projects created outside working hours without "
              "company resources remain yours.", ["O07_ip_assignment"]),
        ],
        outro=["Welcome aboard.", "People Team, Lumen Labs"],
    ),
    Doc(
        name="offer_sales_variable_heavy", kind="offer_letter", style="letter",
        title="APPOINTMENT OFFER",
        intro=["Crestline Retail Solutions, Hyderabad", "Dear Mr. Imran Khan,",
               "We are pleased to appoint you as Business Development Executive."],
        clauses=[
            C("Remuneration", "Your CTC will be Rs. 5,00,000 per annum, of which Rs. 2,40,000 is fixed salary and "
              "Rs. 2,60,000 is performance-linked incentive based on monthly sales targets. Incentives are not "
              "guaranteed.", ["O01_variable_pay"]),
            C("Non-compete", "For a period of 12 months after leaving the Company, you shall not join or work for "
              "any competitor or any client of the Company.", ["O06_non_compete"]),
            C("Changes to terms", "The Company reserves the right to modify your role, targets and salary structure "
              "at its sole discretion.", ["O09_unilateral_change"]),
            C("Notice", "You must give one month's notice. Any dues, including unrecovered advances, will be "
              "deducted from your full and final settlement.", ["O12_final_pay_deduction"]),
            C("Joining bonus", "A joining bonus of Rs. 30,000 is payable with your first salary. This bonus shall be "
              "repaid in full if you resign within one year.", ["O08_relocation_clawback"]),
        ],
        outro=["Regards, HR Department"],
    ),
    Doc(
        name="offer_internship_ppo", kind="offer_letter", style="caps",
        title="INTERNSHIP AND PRE-PLACEMENT OFFER",
        intro=["Quantly Analytics LLP, Mangaluru", "Dear Ms. Meera Shenoy,",
               "Congratulations on your selection for our internship programme with a pre-placement offer."],
        clauses=[
            C("STIPEND", "You will receive a stipend of Rs. 20,000 per month during the six-month internship."),
            C("PRE-PLACEMENT OFFER", "On successful completion, you will be offered a full-time role with a CTC of "
              "Rs. 7,20,000 per annum. The probation period after joining will be twelve months.", ["O05_probation"]),
            C("INTELLECTUAL PROPERTY", "All inventions, code and work product created by you, whether during working "
              "hours or not, shall be the exclusive property of the Company.", ["O07_ip_assignment"]),
            C("NOTICE", "Interns may leave with 15 days' notice. Full-time employees must serve a notice period of "
              "60 days.", ["O03_long_notice"]),
            C("EXIT RESTRICTIONS", "You shall not solicit any client or employee of the Company for two years after "
              "leaving.", ["O06_non_compete"]),
            C("LEAVE", "Interns get one day of leave per month. Holidays follow the company calendar."),
        ],
        outro=["Best wishes, Quantly Analytics"],
    ),
]
