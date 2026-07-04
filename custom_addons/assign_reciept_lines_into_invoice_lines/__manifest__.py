{
    'name': "Invoice for reciepits",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """add stock moves to invoice lines""",
    'description': """""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'account',
        'stock',
    ],
    'data': [
        "views/account_move_views.xml",
    ]
}
