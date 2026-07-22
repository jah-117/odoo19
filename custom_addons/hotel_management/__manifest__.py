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
        'web',
        'website',
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

        "views/food_category_views.xml",
        "views/food_item_views.xml",
        "views/hotel_accommodation_views.xml",
        "views/hotel_room_views.xml",
        "views/room_facility_views.xml",
        "views/order_food_views.xml",
        "views/hotel_guest_views.xml",

        "wizard/make_order_food_views.xml",

        "report/hotel_management_report_views.xml",
        "report/hotel_management_report.xml",

        "views/hotel_management_menus.xml",

        "views/snippets/hotel_management_views.xml",
        "views/snippets/s_hotel_menu_banner.xml",
        "views/snippets/s_hotel_booking_form.xml",
        "views/snippets/s_room_details_carousal.xml",
        "views/snippets/s_room_details.xml",


        "views/snippets/hotel_management_snippets.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'hotel_management/static/src/js/action_manager.js',
        ],
        'web.assets_frontend': [
            'hotel_management/static/src/snippets/*',
            'hotel_management/static/src/js/snippets/*',

        ]
    }
}
