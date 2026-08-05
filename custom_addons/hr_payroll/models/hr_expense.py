#-*- coding: utf-8 -*-
from odoo import fields, models

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payslip_id = fields.Many2one(comodel_name='hr.payslip',string="Payslip")
