{
    'name': "Assignment",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Supply Chain",
    'summary': """add stock moves to invoice lines""",
    'description': """""",
    'sequence': -10,
    'application': True,
    'installable': True,
    'auto_install': True,

    'depends': [
        'mrp',
    ],
    'data': [
        "security/ir.model.access.csv",

        "data/sequence.xml",

        "views/mrp_production_ext_views.xml",
        "views/assignment_2_menus.xml",
    ]
}