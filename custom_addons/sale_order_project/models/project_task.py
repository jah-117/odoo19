from odoo import fields,models

class ProjectTask(models.Model):
    _inherit = 'project.task'

    sale_order_id = fields.Many2one('sale.order',string='Sale Order')

