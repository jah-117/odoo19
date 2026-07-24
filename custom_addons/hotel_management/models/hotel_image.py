from  odoo import fields, models, api

class HotelImage(models.Model):
    _name = 'hotel.image'
    _description = 'Hotel Image'
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    image_1920 = fields.Image()