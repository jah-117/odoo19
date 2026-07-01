from odoo import models,fields

class LowOnStaff(models.TransientModel):
    _name = 'low.on.staff.wizard'

    message = fields.Text()

    def action_approve(self):
        leave = self.env['hr.leave'].search([('id', '=', self.env.context.get('leave_id'))])
        print(self.env.context)
        leave.action_approve()
    def action_refuse(self):
        leave = self.env['hr.leave'].search([('id', '=', self.env.context.get('leave_id'))])
        leave.action_refuse()