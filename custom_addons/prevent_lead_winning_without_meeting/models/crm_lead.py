from odoo import  models,api,_
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _prevent_lead_winning(self,record):
        if record.stage_id.is_won:
            activities = self.env['mail.activity'].search([('active', '=', False), ('res_id', '=', record.id)])
            activity_type = (act.activity_category for act in activities)
            if not 'meeting' in activity_type:
                raise ValidationError(_('Cannot Mark a lead as win without completing atleast one meeting'))