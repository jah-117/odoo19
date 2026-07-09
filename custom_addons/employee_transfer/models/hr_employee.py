from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_create_transfer_request(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select new company',
            'view_mode': 'form',
            'res_model': 'transfer.hr.employee',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
                'default_old_company_id': self.company_id.id,
            }
        }
