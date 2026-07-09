{
    'name': "Product brand in pos",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """""",
    'description': """Show the brand name in pos order line after product name and in receipt""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'product',
        'point_of_sale',
    ],
    'data': [
    "views/product_product_views.xml",
    ],
    'assets':[
        
    ],
}