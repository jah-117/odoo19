#-*- coding: utf-8 -*-
from odoo import fields, models

class HrPayslipInputType(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payroll Input'


    payslip_id = fields.Many2one(comodel_name='hr.payslip', string="Payslip")
    _allowed_input_type_ids = fields.Many2many(comodel_name='hr.payslip.input.type',
                                               related='payslip_id.struct_id.input_line_type_ids')
    input_type_id = fields.Many2one(comodel_name='hr.payslip.input.type',string="Input Type")
    name = fields.Char(string="Description")
    sequence = fields.Integer(string="Sequence",default=10)
    version_id = fields.Many2one(comodel_name='hr.version', string="Version", related='payslip_id.version_id')
    amount = fields.Float(string="Amount")
    code = fields.Char(string="Code")
    date_from = fields.Date(string="Date From",related='payslip_id.date_from')