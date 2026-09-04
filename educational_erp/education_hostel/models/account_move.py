# -*- coding: utf-8 -*-
"""
Invoice for allocations

"""

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    allocation_id = fields.Many2one(comodel_name="edu.hostel.allocation", string="Allocation")
    allocation_state = fields.Selection(related='allocation_id.state', string="Allocation State")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    room_id = fields.Many2one(related='allocation_id.room_id', string="Enrollment")
