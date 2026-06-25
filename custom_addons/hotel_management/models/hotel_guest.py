from odoo import models,fields

class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _inherit = 'res.partner'

    is_hotel_guest = fields.Boolean(string="Hotel Guest",default=False)