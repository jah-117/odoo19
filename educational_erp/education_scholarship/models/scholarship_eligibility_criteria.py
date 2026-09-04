from odoo import models, fields

class ScholarshipEligibilityCriteria(models.Model):
    _name = 'scholarship.eligibility.criteria'
    _description = 'Education Eligibility Criteria'
    _rec_name = 'criteria_id'

    criteria_id = fields.Many2one('education.scholarship.criteria', required=True)
    operator = fields.Selection([
        ('=', 'Equal to'),
        ('!=', 'Not equal to'),
        ('>', 'Greater than'),
        ('>=', 'Greater than or equal to'),
        ('<', 'Less than'),
        ('<=', 'Less than or equal to'),
        ('ilike', 'Contains'),
        ('is_set', 'Is Set'),
        ('in', 'In'),
        ('not in', 'Not in'),
    ], default='=')
    value = fields.Char(string='Value')
    is_require_document = fields.Boolean(string="Need Document",default=False)
