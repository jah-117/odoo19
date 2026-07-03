from  odoo import fields, models,api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    cost_of_task = fields.Float(default=0.0,compute='_compute_effective_hours',store=True)

    @api.depends('timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        if self.timesheet_ids:
            self.cost_of_task = sum(self.timesheet_ids.mapped('total_cost'))