from odoo import fields,models

class HrRuleParameter(models.Model):
    _name = 'hr.rule.parameter'
    _description = 'Rule Parameter'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Html(string='Description')
    parameter_version_ids = fields.One2many(comodel_name='hr.rule.parameter.value',inverse_name='rule_parameter_id')
    # salary_rule_ids = fields.One2many(comodel_name='hr.salary.rule', string='Salary Rules')