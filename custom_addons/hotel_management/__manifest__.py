
{
    'name':"Hotel Management",
    'version': "19.0.1.1",
    'license':"LGPL-3",
    'author':"Cybrosys Trainee",
    'website':"www.odoo.com",
    'category':"Hotel Management",
    'summary':"""Module for managing hotel""",
    'description':"""this is the description part""",
    'sequence':-10,
    'application':True,
    'installable':True,
    'auto_install':True,

    'data':[
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/hotel_management_views.xml",
        "views/hotel_management_menus.xml"
    ]
}