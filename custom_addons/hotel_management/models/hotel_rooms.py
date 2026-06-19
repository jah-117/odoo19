from odoo import models,fields,api

BED_TYPES = [('single',"Single"),('double',"Double"),('dormitory',"Dormitory")]

class HotelRooms(models.Model):
    _name = 'hotel.room'
    _description = 'Details of hotel rooms'
    _rec_name ='room_no_id'

    room_no_id = fields.Integer(string="Room Number",required = True)
    # accommodation_ids = fields.One2many(string="Room Id",comodel_name='hotel.accommodation', inverse_name='room_id')
    bed = fields.Selection(default = 'single',selection=BED_TYPES,string="Bed", required = True)
    available_beds = fields.Integer(string="Available Beds",)
    currency_id = fields.Many2one('res.currency',string="Currency")
    rent = fields.Monetary(string="Rent", currency_field="currency_id")
    facility_ids = fields.Many2many(string="Facility", comodel_name='room.facility')
    state = fields.Selection(string="State",
                             selection=[('available',"Available"),('not_available',"Not Available")],
                             default='available')