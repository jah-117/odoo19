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
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'product_brand_in_pos/static/src/app/component/orderline/orderline.js',
            'product_brand_in_pos/static/src/app/component/orderline/orderline.xml',
            'product_brand_in_pos/static/src/app/component/product_card/product_card.xml',
            'product_brand_in_pos/static/src/app/component/product_card/product_card.xml',
            'product_brand_in_pos/static/src/**/*',
        ],
    }
}
