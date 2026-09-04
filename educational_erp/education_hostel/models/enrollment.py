# -*- coding: utf-8 -*-
from odoo import  models, fields


class EducationEnrollment(models.Model):
    """Student enrollment — one per student per academic year."""

    _inherit = "education.enrollment"

    room_id = fields.Many2one(comodel_name="edu.hostel.room", string="Room No")