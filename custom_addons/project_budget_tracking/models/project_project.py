from  odoo import fields,models,api,_

class ProjectProject(models.Model):
    _inherit = 'project.project'

    budget = fields.Monetary(string="Budget",currency_field='currency_id')
    budget_spend = fields.Monetary(string="Budget Spend",currency_field='currency_id',readonly=True,compute='_compute_budget_spend',store=True)

    @api.depends('task_ids.cost_of_task')
    def _compute_budget_spend(self):
        self.budget_spend = sum(self.task_ids.mapped('cost_of_task'))
        if self.budget_spend / (self.budget if self.budget else self.budget_spend*2 + 1) >= 0.80:
            manager = self.user_id.name if self.user_id else 'Manager'
            self.message_post(
                body=f'Hey {manager}, The project expense has gone over 80% of the budget',
                message_type="notification",
                subtype_xmlid="mail.mt_comment"
            )