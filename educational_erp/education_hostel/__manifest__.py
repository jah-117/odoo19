{
    "name": "Education ERP — Hostel",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Hostel properties, room management, student allocation and occupancy",
    "description": """
Education ERP — Hostel
======================

Hostel properties, room management, student allocation and occupancy.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security", "education_notification", "education_financial_management",
                "mail", "account"],
    "data": [
        "data/hostel_fee_product_data.xml",
        "data/ir_cron_data.xml",
        "data/hostel_fee_templates.xml",
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/hostel_views.xml",
        "views/hostel_invoice_views.xml",
        "views/portal_templates.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 18,
}
