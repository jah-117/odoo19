{
    'name': "Leave request verification",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Human Resources",
    'summary': """Leave restriction if team is understaffed""",
    'description': """this is the description part""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'hr_holidays',
        'hr',
        'mail',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/email_template_data.xml",
        "views/leave_restriction_views.xml",
        "wizard/low_on_staff_wizard.xml",
    ]
}
