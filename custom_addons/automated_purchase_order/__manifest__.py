{
    'name': "Automated Purchase order",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Supply Chain",
    'summary': """add stock moves to invoice lines""",
    'description': """""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'product',
        'purchase',
    ],
    'data': [

        "security/ir.model.access.csv",
        "data/automate_po.xml",
        "views/product_template_views.xml",

        "wizard/automate_po_wizard.xml",
    ]
}