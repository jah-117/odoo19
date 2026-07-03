from odoo import fields, models,api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    hourly_cost = fields.Float(compute='_compute_hourly_cost')
    total_cost = fields.Float(readonly=True,compute='_compute_total_cost')

    @api.onchange('employee_id')
    def _compute_hourly_cost(self):
        self.hourly_cost = self.employee_id.hourly_cost

    @api.depends('unit_amount','hourly_cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.hourly_cost * line.unit_amount

    def unlink(self):
        self.hourly_cost = 0
        return  super().unlink()