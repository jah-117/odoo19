# -*- coding: utf-8 -*-
from odoo import models, fields

class EduNotificationQueue(models.Model):
    _inherit = "edu.notification.queue"

    allocation_id = fields.Many2one(comodel_name="edu.hostel.allocation", string="Allocation")
