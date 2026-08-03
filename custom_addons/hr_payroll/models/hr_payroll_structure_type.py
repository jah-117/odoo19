#-*- coding: utf-8 -*-
from odoo import fields, models

class HrPayrollStructureType(models.Model):
    _name = 'hr.payroll.structure.type'
    _description = 'Payroll Structure Type'

    name = fields.Char(string='Structure Type')
    sequence = fields.Integer(string='Sequence',default=10)
    country_id = fields.Many2one(comodel_name='res.country', string="Country")
    country_code = fields.Char(related='country_id.code', string="Country Code")
    wage_type = fields.Selection([('monthly','Fixed Wage'),('hourly','Hourly Wage')], string='Wage Type',default='monthly')
    default_resource_calendar_id = fields.Many2one(comodel_name='resource.calendar', string='Working Hours')
    default_struct_id = fields.Many2one(comodel_name='hr.payroll.structure', string='Pay Structure')
    default_work_entry_type_id = fields.Many2one(comodel_name='hr.work.entry.type', string='Work Entry Type')