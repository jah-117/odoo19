#-*- coding: utf-8 -*-
{
    'name': "Verification",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Human Resources",
    'summary': """Manage your employee payroll""",
    'sequence': -11,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'base',
       'sale',
    ],
    'data': [
        "views/product_product_views.xml"
    ],
}
