{
    'name': "Sale Order Margin",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """verify that every order line has margin above the threshold""",
    'description': """""",
    'sequence': -50,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'product',
        'sale',
        'web',
    ],
    'data': [
        "views/product_category_views.xml",
        "views/sale_order_views.xml",
    ]
}
