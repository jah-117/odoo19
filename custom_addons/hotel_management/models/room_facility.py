from odoo import models,fields

class RoomFacility(models.Model):
    _name = 'room.facility'
    _description = "Facilities available"

    name = fields.Char(string="Facility", required = True)