from odoo import fields, models

class HrSalaryRuleInputSelection(models.Model):
    _name = 'hr.salary.rule.input.selection'

    key = fields.Char(string='Key')
    value = fields.Char(string='Value')
    