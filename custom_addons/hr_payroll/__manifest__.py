{
    'name': "Pyroll",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Human Resources",
    'summary': """Manage your employee payroll""",
    'sequence': -11,
    'application': True,
    'installable': True,
    'auto_install': True,

    'depends': [
        'hr',
        'hr_holidays',
        'hr_work_entry',
        'hr_attendance',
        'resource',
    ],
    'data': [
        "security/ir.model.access.csv",

        "views/hr_employee_type_views.xml",
        "views/hr_payroll_views.xml",
    ],
}
