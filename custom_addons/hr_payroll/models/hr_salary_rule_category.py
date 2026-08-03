#-*- coding: utf-8 -*-
from odoo import fields, models

class HrSalaryRuleCategory(models.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    parent_id = fields.Many2one(comodel_name='hr.salary.rule.category',string="Parent")
    country_id = fields.Many2one(comodel_name='res.country',string='Country')
    salary_rule_ids = fields.Many2many(comodel_name='hr.salary.rule')

    def action_open_salary_rules(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.salary.rule',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.salary_rule_ids.ids)],
        }