#-*- coding: utf-8 -*-
from odoo import fields, models

class HrPayslipInputType(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payroll Input'


    payslip_id = fields.Many2one(comodel_name='hr.payroll', string="Payroll")