from odoo import models,fields

class HotelGuest(models.Model):
    _name = 'hotel.guest'

    name = fields.Char(string="Name", required=True)
    age = fields.Integer(string="Age")
    gender = fields.Selection([('male', "Male"),('female', "Female")],string="Gender")