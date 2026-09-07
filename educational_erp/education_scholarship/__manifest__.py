{
    "name": "Education ERP — Scholarships",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Scholarship applications, review workflow and fee allocation",
    "description": """
Education ERP — Scholarships
============================

Scholarship applications, review workflow and fee allocation.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ['education_core', 'education_financial_management', 'portal','website'],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/scholarship_cron.xml",
        "data/scholarship_product_data.xml",
        "views/scholarship_views.xml",
        "views/scholarship_criteria_views.xml",
        "views/scholarship_eligibility_criteria_view.xml",
        "views/scholarship_application_views.xml",
        "views/scholarship_bill_views.xml",
        "views/scholarship_menus.xml",
        "views/portal_templates.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 17,
}
