#-*- coding: utf-8 -*-
from odoo import fields, models

class HrSalaryRuleInputSelection(models.Model):
    _name = 'hr.salary.rule.input.selection'
    _description = 'Salary Rule Input Selection'

    key = fields.Char(string='Key')
    value = fields.Char(string='Value')
    sequence = fields.Integer(string='Sequence',default=10)
    