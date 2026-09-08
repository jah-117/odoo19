# -*- coding: utf-8 -*-
from odoo import fields, models


class DisciplinaryAction(models.Model):
    _name = "education.disciplinary.action"
    _description = "Disciplinary Action"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
