"""
Small, hand-labeled dataset for demonstrating LoRA fine-tuning: classify
a risk-factor-style sentence into one of the risk categories we already
discovered via LLM extraction in the knowledge graph milestone. This
mirrors that exact task, but as a fine-tuned classifier instead of an
LLM prompt — the actual comparison this demo is built to illustrate.
"""

LABELS = ["supply_chain", "regulatory", "competition", "cybersecurity", "macroeconomic"]

TRAIN_EXAMPLES = [
    ("The Company relies on single-source suppliers for critical components.", "supply_chain"),
    ("Disruptions in the supply chain could delay product manufacturing.", "supply_chain"),
    ("The Company depends on outsourcing partners located outside the U.S.", "supply_chain"),
    ("Component shortages may affect the Company's ability to meet demand.", "supply_chain"),

    ("The Company is subject to antitrust laws and regulatory scrutiny.", "regulatory"),
    ("New data privacy regulations could increase compliance costs.", "regulatory"),
    ("Government agencies may impose fines for non-compliance.", "regulatory"),
    ("Changes in international trade law could affect operations.", "regulatory"),

    ("Competitors offer similar products at lower prices.", "competition"),
    ("The Company faces significant competition from larger rivals.", "competition"),
    ("Market share could decline due to aggressive competitor pricing.", "competition"),
    ("New entrants continue to challenge the Company's market position.", "competition"),

    ("The Company's systems may be vulnerable to hacking and ransomware.", "cybersecurity"),
    ("A data breach could expose confidential customer information.", "cybersecurity"),
    ("Cyberattacks could disrupt critical business operations.", "cybersecurity"),
    ("Third parties with system access increase security risk exposure.", "cybersecurity"),

    ("Inflation and currency fluctuations could affect profitability.", "macroeconomic"),
    ("A global economic downturn may reduce consumer spending.", "macroeconomic"),
    ("Rising interest rates could increase the Company's borrowing costs.", "macroeconomic"),
    ("Geopolitical instability may disrupt international markets.", "macroeconomic"),
]

EVAL_EXAMPLES = [
    ("The Company may be unable to source enough raw materials from its vendors.", "supply_chain"),
    ("New privacy legislation in the EU could impose additional obligations.", "regulatory"),
    ("Rivals with lower cost structures threaten the Company's pricing power.", "competition"),
    ("Unauthorized access to Company systems could compromise user data.", "cybersecurity"),
    ("A recession could reduce demand for the Company's premium products.", "macroeconomic"),
]
