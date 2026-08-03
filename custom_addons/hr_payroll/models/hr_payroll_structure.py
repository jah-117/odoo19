#-*- coding: utf-8 -*-
from odoo import fields, models
class HrPayrollStructure(models.Model):
    _name = 'hr.payroll.structure'
    _description = 'Payroll Structure'

    name = fields.Char(string="Structure Name")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string="Sequence",default=10)
    employee_type_ids = fields.Many2many(comodel_name='hr.employee.type',string="Employee Types")
    type_id = fields.Many2one(comodel_name='hr.payroll.structure.type',string="Type")
    use_worked_day_lines = fields.Boolean(string="Use Worked Day Lines", default=True)
    country_id = fields.Many2one(comodel_name='res.country', string="Country")
    country_code = fields.Char(related='country_id.code', string="Country Code")
    report_id = fields.Many2one(comodel_name='ir.actions.report', string="Template")
    payslip_name = fields.Char(string="Payslip Name")
    hide_basic_on_pdf = fields.Boolean(string="Hide Basics On PDF",default=False)
    input_line_type_ids = fields.Many2many(comodel_name='hr.payslip.input.type',string="Other Input Lines")
    rule_ids= fields.Many2many(comodel_name='hr.salary.rule',string="Salary Rules")
    unpaid_work_entry_type_ids = fields.Many2many('hr.work.entry.type',string="Unpaid Time Types")
    ytd_computation = fields.Boolean(string="Year to Date Computation",default=False)

