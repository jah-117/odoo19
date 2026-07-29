from odoo import http, fields
from odoo.http import request


class FoodCartController(http.Controller):

    @http.route('/load_user_data', type='jsonrpc', website=True, auth='user')
    def load_user_data(self):
        accommodation_id = request.env['hotel.accommodation'].sudo().search(
            [('guest', '=', request.env.user.partner_id.id), ('state', '=', 'check_in')])
        if not accommodation_id:
            return {
                'uid': request.session.uid,
                'code': 404,
                'error': 'No accommodation found, Please complete check in procedure or contact reception',
                'redirect_url': '/hotel_management',
                'partner_id': request.env.user.partner_id.id,
            }
        return {
            'uid': request.session.uid,
            'code': 200,
            'message': 'Success',
            'accommodation_id': accommodation_id.id,
            'partner_id': request.env.user.partner_id.id,
        }

    @http.route('/add_to_cart', type='jsonrpc', website=True, auth='user')
    def add_to_cart(self, item_id, cart_id, accommodation_id):
        item = request.env['food.items'].sudo().browse(int(item_id))
        item.quantity = item.quantity - 1
        if item.quantity < 0:
            item.quantity = 0
            return {
                'code': 400,
                'message': f'No more quantity of {item.name} available.',
            }
        if cart_id:
            cart = request.env['website.cart'].sudo().browse(int(cart_id))
            order = cart.food_order_line_ids.filtered(lambda order: order.food_item_id.id == item.id)
            if order:
                order.quantity = order.quantity + 1
                order.subtotal = order.quantity * order.unit_price
            else:
                cart.update({
                    'food_order_line_ids': [
                        fields.Command.create({
                            'food_item_id': item.id,
                            'quantity': 1,
                            'subtotal': item.price,
                        })
                    ]
                })
        else:
            accommodation = request.env['hotel.accommodation'].sudo().browse(int(accommodation_id))
            cart = request.env['website.cart'].sudo().create({
                'accommodation_id': accommodation.id,
                'user_id': request.session.uid,
            })
            cart.update({
                'food_order_line_ids': [
                    fields.Command.create({
                        'food_item_id': item.id,
                        'quantity': 1,
                        'subtotal': item.price,
                    })
                ]
            })
        return {
            'code': 200,
            'message': 'Successfully added to cart',
            'total': cart.compute_total(),
        }

    @http.route('/remove_from_cart', type='jsonrpc', website=True, auth='user')
    def remove_from_cart(self, order_id, cart_id):
        order = request.env['food.order.lines'].sudo().browse(int(order_id)).unlink()
        return {
            'ok': order,
            'message': 'Successfully removed from cart' if order else 'Error, Unable to remove from cart',
            'total': request.env['website.cart'].sudo().browse(int(cart_id)).compute_total(),
        }

    @http.route('/update_quantity', type='jsonrpc', website=True, auth='user')
    def update_quantity(self, order_id, is_increment):
        order = request.env['food.order.lines'].sudo().browse(int(order_id))
        order.food_item_id.quantity = order.food_item_id.quantity - 1 if is_increment else order.food_item_id.quantity + 1
        if order.food_item_id.quantity < 0:
            order.food_item_id.quantity = 0
            return {
                'code': 400,
                'message': f'No more quantity of {order.food_item_id.name} available.',
            }
        order.quantity = order.quantity + 1 if is_increment else order.quantity - 1
        order.subtotal = order.quantity * order.unit_price
        return {
            'code': 200,
            'message': 'Successfully updated quantity.',
            'quantity': order.quantity,
            'subtotal': order.subtotal,
            'total': order.website_cart_id.compute_total(),
        }

    @http.route('/confirm_order', type='jsonrpc', website=True, auth='user')
    def confirm_order(self, cart_id):
        res, error = request.env['website.cart'].sudo().browse(int(cart_id)).confirm_order()
        return {
            'code': 200 if res else 400,
            'message': 'Successfully placed order.' if res else 'Error, Unable to confirm order.',
            'error': error,
        }
