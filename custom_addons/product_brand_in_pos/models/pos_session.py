from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_order(self):
        result = super()._loader_params_pos_order()
        result["search_params"]["fields"].append("brand")
        result["search_params"]["fields"].append("credit_limit")
        return result