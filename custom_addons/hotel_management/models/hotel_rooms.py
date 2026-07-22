from odoo import models,fields,api

BED_TYPES = [('single',"Single"),('double',"Double"),('dormitory',"Dormitory")]

class HotelRooms(models.Model):
    _name = 'hotel.room'
    _description = 'Details of hotel rooms'
    _rec_name ='room_no_id'

    room_no_id = fields.Integer(string="Room Number",required = True,aggregator=False,help="Room Number.")
    bed = fields.Selection(default = 'single',selection=BED_TYPES,string="Bed", required = True,help="Type of bed in this room.")
    available_beds = fields.Integer(string="Available Beds",help="If dormitory type: Total number of beds available.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency',string="Currency", related='company_id.currency_id')
    rent = fields.Monetary(string="Rent", currency_field="currency_id",aggregator=False, help="Rental amount per day.")
    facility_ids = fields.Many2many(string="Facility", comodel_name='room.facility',help="Facilities available for this room.")
    state = fields.Selection(string="State",
                             selection=[('available',"Available"),
                                        ('not_available',"Not Available")],
                             default='available',
                             help="Room availability state.")
    @api.model
    def get_available_rooms(self,bed_type):
        available_rooms = self.search([('state','=','available'),('bed','=',bed_type)])
        return [
            {'room_no': room.room_no_id,
            'room_id': room.id,}
            for room in available_rooms
        ] if available_rooms else {}
    @api.model
    def get_room_details(self):
        rooms = self.search([],limit=4)
        return [
            {'room_no':room.room_no_id,
             'bed_type':room.bed,
             'rent':room.rent,
             'facilities':[fac.name for fac in room.facility_ids],
             'state':room.state,
            } for room in rooms
        ]