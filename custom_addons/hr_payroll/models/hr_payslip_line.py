#-*- coding: utf-8 -*-
from odoo import fields, models

class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'

    payslip_id = fields.Many2one(comodel_name='hr.payslip', string="Payslip")
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    salary_rule_id = fields.Many2one(comodel_name='hr.salary.rule', string="Salary Rule")
    category_ids = fields.Many2many(comodel_name='hr.salary.rule.category',related='salary_rule_id.category_ids',string="Categories")
    sequence = fields.Integer(string="Sequence",default=10)
    quantity = fields.Float(string="Quantity")
    rate = fields.Float(string="Rate (%)")
    company_id = fields.Many2one(comodel_name='res.company',string="Company")
    currency_id = fields.Many2one(comodel_name='res.currency',string="Currency",related='company_id.currency_id')
    amount = fields.Monetary(string="Base",currency_field="currency_id")
    amount_fix = fields.Float(string="Fixed Amount",related='salary_rule_id.amount_fix')
    amount_percentage = fields.Float(string="Percentage (%)",related='salary_rule_id.amount_percentage')
    amount_select = fields.Selection(string="Amount Type",related='salary_rule_id.amount_select')
    total = fields.Monetary(string="Total",currency_field="currency_id")
    ytd = fields.Monetary(string="YTD",currency_field="currency_id")


