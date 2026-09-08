# -*- coding: utf-8 -*-
from odoo import fields, models


class SchoolRule(models.Model):
    _name = "education.school.rule"
    _description = "School Rule"

    name = fields.Char(string="Rule Title", required=True)
    description = fields.Text(string="Description", required=True)
    category = fields.Selection(
        [
            ("general", "General"),
            ("academic", "Academic"),
            ("uniform", "Uniform"),
            ("conduct", "Conduct"),
            ("other", "Other"),
        ],
        string="Category",
        default="general",
        required=True,
    )
    active = fields.Boolean(default=True)
