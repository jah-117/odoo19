{
    'name': "Crm lead prevention",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Sales",
    'summary': """Prevent a CRM lead from reaching "Won" without a meeting""",
    'description': """Check the lead's chatter/activities before marking as Won
If no meeting-type activity has been completed, raise a validation error
Display the count of completed meetings in the lead form
Allow CRM managers to override this restriction""",
    'sequence': -10,
    'application': False,
    'installable': True,
    'auto_install': True,

    'depends': [
        'crm',
        'base_automation',
    ],
    'data': [
        "data/automated_actions.xml",
        "views/crm_lead_views.xml",
    ]
}
