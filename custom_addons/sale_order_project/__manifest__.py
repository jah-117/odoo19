{
    'name': "Sale Order Task",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """create task on sale order""",
    'description': """""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'sale',
        'project',
    ],
    'data': [
        "views/tasks_list_view.xml",
        "views/sale_order_views.xml",
    ]
}
