from odoo import fields, models,api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    hourly_cost = fields.Float(related='employee_id.hourly_cost')
    total_cost = fields.Float(readonly=True,compute='_compute_total_cost')

    @api.onchange('unit_amount','hourly_cost')
    def _compute_total_cost(self):
        self.total_cost = self.hourly_cost * self.unit_amount