from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        msg = {}
        failed_orders = False
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            price_log = ''
            chatter_log = ''
            noprice = False
            for order_line in self.order_line:
                if not order_line.product_id.standard_price:
                    noprice = True
                    failed_orders = True
                    price_log += f'{order_line.product_id.name} has zero cost.\n'
                if order_line.margin_threshold < order_line.categ_id.minimum_margin_percent:
                    failed_orders = True
                    chatter_log += f'''The {order_line.product_id.name} has failed the margin check.\n
                Minimum margin percentage: {order_line.categ_id.minimum_margin_percent :.2f}%.\n
                {order_line.product_id.name} margin: {order_line.margin_threshold:.2f}%.\n'''
            if failed_orders: self.message_post(
                body=chatter_log if not noprice else price_log,
            )
            msg = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Low Margin Threshold!',
                    'message': chatter_log,
                    'type': 'danger',
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            } if not noprice else {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Unable to Calculate margin!',
                    'message': price_log,
                    'type': 'danger',
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        return msg if failed_orders else super().action_confirm()
