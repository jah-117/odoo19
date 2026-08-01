{
    'name': "Employee loan management",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Human Resources",
    'summary': """Manage your employee Loan""",
    'sequence': -11,
    'application': True,
    'installable': True,
    'auto_install': True,

    'depends': [
        'hr',
    ],
    'data': [
        "security/ir.model.access.csv",

        "data/sequence.xml",

        "views/employee_loan_views.xml",
        "views/employee_loan_line_views.xml",
        "views/hr_employee_views.xml",

        "views/loan_views.xml",
    ],
}
