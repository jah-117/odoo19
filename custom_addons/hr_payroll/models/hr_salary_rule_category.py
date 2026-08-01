from odoo import fields, models

class HrSalaryRuleCategory(models.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    country_id = fields.Many2one(comodel_name='res.country',string='Country')
    salary_rule_ids = fields.Many2many(comodel_name='hr.salary.rule')