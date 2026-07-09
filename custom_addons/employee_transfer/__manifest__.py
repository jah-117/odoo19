{
    'name': 'Employee Transfer',
    'version': '1.0',
    'summary': 'Employee Transfer',
    'author': '',
    'website': '',
    'license': "LGPL-3",
    'category': 'Human Resources',
'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,
    'depends': ['hr'],
    'data': [
        "security/employee_transfers_rule.xml",
        "security/ir.model.access.csv",
        "views/employee_transfer_views.xml",
        "views/hr_employee_views.xml",
        "wizard/transfer_hr_employee_views.xml",
    ]
}