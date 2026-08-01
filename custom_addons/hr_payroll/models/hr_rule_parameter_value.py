from odoo import fields,models

class HrRuleParameterValue(models.Model):
    _name = 'hr.rule.parameter.value'
    _description = 'Rule Parameter Value'

    code = fields.Char(string='Code', readonly=True)
    rule_parameter_id = fields.Many2one(comodel_name='hr.rule.parameter',string='Rule Parameter')
    rule_parameter_name = fields.Char(string='Name')
