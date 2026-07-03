{
    'name': "Project budget tracking",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Human Resources",
    'summary': """Project budget tracking with timesheet cost alerts""",
    'description': """this is the description part""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'project',
        'hr_timesheet',
        'hr',
        'analytic',
    ],
    'data': [
        "views/project_project_views.xml",
        "views/project_task_views.xml",
        "views/account_analytic_line_views.xml",
    ]
}
