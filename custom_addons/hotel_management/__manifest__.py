{
    'name': "Hotel Management",
    'version': "19.0.1.1",
    'license': "LGPL-3",
    'author': "Cybrosys Trainee",
    'website': "www.odoo.com",
    'category': "Hotel Management",
    'summary': """Module for managing hotel""",
    'description': """this is the description part""",
    'sequence': -10,
    'application': True,
    'installable': True,
    'auto_install': True,

    'depends': [
        'product',
        'mail',
        'account',
        'base_automation',
        'lunch',
    ],
    'data': [
        "security/hotel_management_groups.xml",
        "security/hotel_management_rules.xml",
        "security/ir.model.access.csv",

        "data/sequence.xml",
        "data/room_and_facility_data.xml",
        "data/ir_cron_data.xml",
        "data/checkout_remainder_mail_template.xml",
        "data/server_actions.xml",

        "views/food_category_view.xml",
        "views/food_item_view.xml",
        "views/hotel_accommodation_view.xml",
        "views/hotel_room_view.xml",
        "views/room_facility_views.xml",
        "views/order_food_views.xml",
        "views/hotel_guest_views.xml",

        "wizard/order_food_transient_views.xml",

        "menus/hotel_management_menus.xml"
    ]
}
