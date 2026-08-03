#-*- coding: utf-8 -*-
from odoo import api, fields, models

class HrPayslipInputType(models.Model):
    _name = 'hr.payslip.input.type'
    _description = 'Payroll Input Type'

    active = fields.Boolean(default=True, string='Active')
    name = fields.Char(string="Name")
    available_in_attachments = fields.Boolean(default=False, string='Available in Attachments')
    code = fields.Char(string='Code')
    struct_ids = fields.One2many(comodel_name='hr.payroll.structure',string='Availability in Structure', inverse_name='input_line_type_ids')
    is_quantity = fields.Boolean(string='Is Quantity')
    default_no_end_date = fields.Boolean(string='No end date by default')

