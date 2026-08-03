#-*- coding: utf-8 -*-
from odoo import fields,models,api
import re

class HrRuleParameter(models.Model):
    _name = 'hr.rule.parameter'
    _description = 'Rule Parameter'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Html(string='Description')
    parameter_version_ids = fields.One2many(comodel_name='hr.rule.parameter.value',inverse_name='rule_parameter_id')
    current_value_one_line = fields.Text(string='Current Value',readonly=True,compute='_compute_current_value_one_line')
    valid_since = fields.Date(string='Valid Since', compute='_compute_valid_since',readonly=True)
    salary_rule_ids = fields.One2many(comodel_name='hr.salary.rule', string='Salary Rules', inverse_name='parameter_id')
    salary_rule_count = fields.Integer(string='Salary Rules Count',compute='_compute_count')

    def action_open_salary_rules(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.salary.rule',
            'domain': [('id', 'in', self.salary_rule_ids.ids)],
            'view_mode': 'list,form',
        }

    def _compute_current_value_one_line(self):
        self.current_value_one_line = self.parameter_version_ids[0].parameter_value if not len(re.findall("[([{]",self.parameter_version_ids[0].parameter_value)) else '(...)'

    def _compute_valid_since(self):
        self.valid_since = self.parameter_version_ids[0].date_from

    def _compute_count(self):
        self.salary_rule_count = len(self.salary_rule_ids)
