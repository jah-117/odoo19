from odoo import fields,models

class HrSalaryRuleSection(models.Model):
    _name = 'hr.salary.rule.section'
    _description = 'Salary Rule Section'

    name = fields.Char(string='Name')
    struct_ids = fields.Many2many(comodel_name='hr.payroll.structure',string='Available in Salary Structures')
    