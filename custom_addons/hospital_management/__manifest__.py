{
    'name': "Hospital Management",
    'version': "1.0.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Hospital Management",
    'summary': """Module for managing hospital""",
    'description': """this is the description part""",
    'sequence': -11,
    'application': True,
    'installable': True,
    'auto_install': True,

    'depends': [
        'product',
        'hr',
        'base_automation',
    ],

    'data': [
        "security/ir.model.access.csv",

        "data/ir_sequence.xml",
        "data/prevent_completed_appointment_deletion.xml",
        "data/patient_state_automation.xml",

        "views/hospital_appointment_views.xml",
        "views/hospital_departments_views.xml",
        "views/hospital_patient_views.xml",
        "views/hospital_doctor_views.xml",

        "views/hospital_management_menus.xml",
    ]
}
