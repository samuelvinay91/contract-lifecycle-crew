"""Mock contract texts for demonstration and testing.

Each contract is 200-400 words and contains realistic clauses, some of
which are intentionally risky to exercise the risk-assessment pipeline.
"""

from __future__ import annotations

SAAS_AGREEMENT = """\
SOFTWARE-AS-A-SERVICE AGREEMENT

This SaaS Agreement ("Agreement") is entered into as of January 15, 2025, \
by and between CloudTech Solutions Inc. ("Provider") and Acme Corporation ("Customer").

1. TERM AND RENEWAL
This Agreement shall commence on the Effective Date and continue for an initial \
term of twelve (12) months. This Agreement shall automatically renew for successive \
twelve-month periods unless either party provides written notice of non-renewal at \
least thirty (30) days prior to the end of the then-current term.

2. PAYMENT TERMS
Customer shall pay Provider a monthly subscription fee of $25,000. Payment is due \
within thirty (30) days of invoice. Late payments shall accrue interest at 1.5% per month.

3. SERVICE LEVEL AGREEMENT
Provider guarantees 99.5% uptime availability measured monthly. In the event of \
downtime exceeding this threshold, Customer shall receive service credits equal to \
10% of the monthly fee for each additional 0.1% of downtime.

4. LIMITATION OF LIABILITY
PROVIDER'S TOTAL LIABILITY UNDER THIS AGREEMENT SHALL BE UNLIMITED AND SHALL \
INCLUDE ALL DIRECT, INDIRECT, CONSEQUENTIAL, AND INCIDENTAL DAMAGES ARISING FROM \
ANY CAUSE WHATSOEVER.

5. CONFIDENTIALITY
Each party agrees to maintain the confidentiality of all proprietary information \
disclosed by the other party. This obligation shall survive termination for a period \
of five (5) years.

6. INTELLECTUAL PROPERTY
All intellectual property created during the performance of this Agreement shall be \
owned exclusively by Provider, including any customizations or integrations developed \
for Customer.

7. TERMINATION
Either party may terminate this Agreement for cause upon sixty (60) days written \
notice if the other party materially breaches any provision and fails to cure within \
thirty (30) days. Provider may terminate this Agreement without cause upon thirty \
(30) days written notice.

8. INDEMNIFICATION
Customer shall indemnify and hold harmless Provider from any and all claims, damages, \
losses, and expenses arising from Customer's use of the Service.

9. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.

Total Contract Value: $300,000 annually.
"""

NDA_AGREEMENT = """\
MUTUAL NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of March 1, 2025, \
by and between DataVault Technologies LLC ("Party A") and InnovateCo Inc. ("Party B").

1. DEFINITION OF CONFIDENTIAL INFORMATION
"Confidential Information" means ALL information disclosed by either party in ANY \
form whatsoever, including but not limited to business plans, financial data, customer \
lists, technical specifications, source code, algorithms, marketing strategies, \
employee information, and any information that a reasonable person would consider \
confidential. Confidential Information also includes any information derived from, \
or that could lead to the discovery of, the disclosing party's proprietary technology.

2. OBLIGATIONS
The receiving party shall: (a) protect Confidential Information using the same degree \
of care it uses for its own confidential information, but no less than reasonable care; \
(b) not disclose Confidential Information to any third party without prior written \
consent; (c) use Confidential Information solely for the Purpose defined herein.

3. TERM AND SURVIVAL
This Agreement shall remain in effect for three (3) years from the Effective Date. \
The confidentiality obligations shall survive termination for a period of ten (10) years.

4. NON-COMPETE
During the term of this Agreement and for a period of thirty-six (36) months following \
termination, neither party shall directly or indirectly compete with the other party \
in any market segment where the other party operates, worldwide.

5. REMEDIES
The parties acknowledge that a breach of this Agreement may cause irreparable harm. \
The non-breaching party shall be entitled to injunctive relief, specific performance, \
and monetary damages including attorney fees and costs.

6. NON-SOLICITATION
For twenty-four (24) months after termination, neither party shall solicit or hire any \
employee or contractor of the other party.

7. GOVERNING LAW
This Agreement shall be governed by the laws of the State of California.
"""

VENDOR_MSA = """\
MASTER SERVICE AGREEMENT

This Master Service Agreement ("Agreement") is entered into as of February 10, 2025, \
by and between GlobalServ Corp. ("Vendor") and TechStart Inc. ("Client").

1. SCOPE OF SERVICES
Vendor shall provide managed IT infrastructure services including cloud hosting, \
database administration, network monitoring, and security operations as detailed in \
each Statement of Work ("SOW") executed under this Agreement.

2. SERVICE LEVELS
Vendor guarantees the following service levels: (a) 99.99% infrastructure availability; \
(b) response time of 15 minutes for critical incidents; (c) resolution time of 4 hours \
for critical incidents; (d) monthly reporting on all SLA metrics. Failure to meet SLA \
targets shall result in service credits of 5% of monthly fees per missed metric.

3. PAYMENT
Client shall pay Vendor a base monthly fee of $50,000 plus usage-based charges as \
defined in each SOW. Payment terms are Net 45.

4. TERM
Initial term of twenty-four (24) months commencing on the Effective Date.

5. TERMINATION
Client may terminate this Agreement for convenience upon ninety (90) days written \
notice, subject to an early termination fee equal to three (3) months of base fees. \
Vendor may terminate only for cause after a sixty (60) day cure period.

6. LIMITATION OF LIABILITY
Each party's total aggregate liability under this Agreement shall not exceed the \
total fees paid or payable during the twelve (12) months preceding the claim.

7. DATA PROTECTION
Vendor shall comply with all applicable data protection regulations including GDPR \
and CCPA. Vendor shall maintain SOC 2 Type II certification throughout the term.

8. INTELLECTUAL PROPERTY
All pre-existing IP remains with the owning party. Work product created under an \
SOW shall be owned by Client upon full payment.

9. INDEMNIFICATION
Each party shall indemnify the other against third-party claims arising from the \
indemnifying party's negligence or willful misconduct.

10. GOVERNING LAW
This Agreement shall be governed by the laws of the State of New York.

Total Contract Value: $1,200,000 annually.
"""

EMPLOYMENT_AGREEMENT = """\
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into as of April 1, 2025, \
by and between TechForward Inc. ("Company") and Jane Smith ("Employee").

1. POSITION AND DUTIES
Employee shall serve as Senior Software Engineer reporting to the VP of Engineering. \
Employee's duties shall include software development, code review, mentoring junior \
engineers, and contributing to architectural decisions.

2. COMPENSATION
Company shall pay Employee an annual base salary of $185,000, payable in accordance \
with Company's standard payroll schedule. Employee shall be eligible for an annual \
performance bonus of up to 15% of base salary.

3. BENEFITS
Employee shall be eligible to participate in Company's standard benefits programs \
including health insurance, dental insurance, 401(k) with 4% match, and twenty (20) \
days of paid time off per year.

4. EQUITY
Employee shall receive a stock option grant of 10,000 shares vesting over four (4) \
years with a one-year cliff, subject to the terms of Company's Equity Incentive Plan.

5. CONFIDENTIALITY
Employee agrees to maintain the confidentiality of all Company proprietary information \
during and after employment. This obligation survives termination indefinitely for \
trade secrets and for two (2) years for other confidential information.

6. INTELLECTUAL PROPERTY
All inventions, works of authorship, and discoveries made by Employee during the \
course of employment and related to Company's business shall be owned by Company.

7. NON-COMPETE
For twelve (12) months following termination, Employee shall not work for a direct \
competitor of Company within the United States.

8. NON-SOLICITATION
For twelve (12) months following termination, Employee shall not solicit Company \
employees or customers.

9. TERMINATION
Either party may terminate this Agreement at will with two (2) weeks written notice. \
Company may terminate immediately for cause.

10. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Washington.

Total Compensation Value: approximately $230,000 annually.
"""

# Mapping of contract type identifiers to their full text
MOCK_CONTRACTS: dict[str, str] = {
    "saas_agreement": SAAS_AGREEMENT,
    "nda": NDA_AGREEMENT,
    "vendor_msa": VENDOR_MSA,
    "employment": EMPLOYMENT_AGREEMENT,
}
