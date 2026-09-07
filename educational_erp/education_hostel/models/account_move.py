# -*- coding: utf-8 -*-
"""
Invoice for allocations

"""

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    allocation_id = fields.Many2one(
        comodel_name="edu.hostel.allocation",
        string="Allocation",
        index=True
    )
    allocation_state = fields.Selection(
        related='allocation_id.state',
        string="Allocation State",
        store=True,
        readonly=True,
        index=True,
    )
    room_id = fields.Many2one(
        related='allocation_id.room_id',
        string="Room",
        store=True,
        readonly=True,
    )
    invoice_type = fields.Selection(
        selection_add=[('hostel_fee', 'Hostel Fee')],
    )
