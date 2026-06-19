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
        'mail',
    ],
    'data': [
        "security/ir.model.access.csv",

        "data/sequence.xml",

        "views/food_category_view.xml",
        "views/food_item_view.xml",
        "views/hotel_accommodation_view.xml",
        "views/hotel_room_view.xml",
        "views/room_facility_views.xml",
        # "wizard/attachment_not_found.xml",

        "menus/hotel_management_menus.xml"
    ]
}
