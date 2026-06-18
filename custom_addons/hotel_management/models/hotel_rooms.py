from odoo import models,fields

class HotelRooms(models.Model):
    _name = 'hotel.room'
    _description = 'Details of hotel rooms'


    roomNo = fields.Integer(string="Room Number",required = True)
    bed = fields.Selection(default = 'single',selection=[('single',"Single"),('double',"Double"),('dormitory',"Dormitory")],string="Bed", required = True)
    availableBeds = fields.Integer(string="Available Beds",tracking=True)
    currency_id = fields.Many2one('res.currency',string="Currency")
    rent = fields.Monetary(string="Rent", currency_field="currency_id")
    facility_id = fields.Many2many(string="Facility", comodel_name='room.facility')
    state = fields.Selection(string="State",selection=[('available',"Available"),('not_available',"Not Available")],default='available')
