from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_not_allowed = fields.Boolean(string="Loan Not Allowed", default=False)
