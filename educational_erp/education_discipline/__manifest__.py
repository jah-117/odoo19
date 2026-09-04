{
    "name": "Education ERP — Discipline",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Disciplinary incidents, inspection logs and action tracking",
    "description": """
Education ERP — Discipline
==========================

Disciplinary incidents, inspection logs and action tracking.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ['education_core', 'portal'],
    "data": [
        "security/discipline_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/discipline_default_data.xml",
        "views/portal_templates.xml",
        "views/violation_type_views.xml",
        "views/disciplinary_action_views.xml",
        "views/school_rule_views.xml",
        "views/discipline_case_views.xml",
        "views/enrollment_views.xml",
        "views/discipline_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 14,
}
