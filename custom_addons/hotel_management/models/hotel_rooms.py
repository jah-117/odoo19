from odoo import models,fields

BED_TYPES = [('single',"Single"),('double',"Double"),('dormitory',"Dormitory")]

class HotelRooms(models.Model):
    _name = 'hotel.room'
    _description = 'Details of hotel rooms'
    _rec_name ='room_no_id'

    room_no_id = fields.Integer(string="Room Number",required = True)
    bed = fields.Selection(default = 'single',selection=BED_TYPES,string="Bed", required = True)
    available_beds = fields.Integer(string="Available Beds",)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency',string="Currency", related='company_id.currency_id')
    rent = fields.Monetary(string="Rent", currency_field="currency_id")
    facility_ids = fields.Many2many(string="Facility", comodel_name='room.facility')
    state = fields.Selection(string="State",
                             selection=[('available',"Available"),('not_available',"Not Available")],
                             default='available')

