from odoo import fields, models

class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'

    payslip_id = fields.Many2one(comodel_name='hr.payslip', string="Payslip")