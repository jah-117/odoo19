{
    'name': "Product quantity in pos",
    'version': "19.0.1.0.0",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """""",
    'description': """Show the product quantity in pos avialble in specified location""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,
    'pre_init_hook':'_enable_storage_locations',

    'depends': [
        'product',
        'point_of_sale',
        'stock',
    ],
    'data': [
        "views/res_config_settings_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'product_quantity_in_pos/static/src/*',
        ],
    }
}
