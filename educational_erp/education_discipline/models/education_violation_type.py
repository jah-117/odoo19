# -*- coding: utf-8 -*-
from odoo import fields, models


class ViolationType(models.Model):
    _name = "education.violation.type"
    _description = "Violation Type"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
