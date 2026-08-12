{
    'name': "Filter tree view",
    'version': "1.0.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """""",
    'description': """""",
    'sequence': -11,
    'application': False,
    'installable': True,
    'auto_install': False,

    'depends': [
        'crm',
    ],

    'data': [
        "views/crm_lead_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'filter_tree_view/static/src/**/*',
        ],
    }
}
