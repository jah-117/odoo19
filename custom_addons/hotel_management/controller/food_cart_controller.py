from odoo import http,fields
from odoo.http import request


class FoodCartController(http.Controller):
    @http.route('/get_cart_data', type='json', website=True, auth='user')
    def get_cart_data(self):
        accommodation_id = request.env['hotel.accommodation'].sudo().search(
            [('guest', '=', request.env.user.partner_id.id), ('state', '=', 'check_in')])
        if not accommodation_id:
            return {
                'uid': request.session.uid,
                'code': 404,
                'error': 'No accommodation found, Please complete check in procedure or contact reception',
                'redirect_url': '/hotel_management'
            }
        cart_id = request.env['website.cart'].sudo().search(
            [('user_id', '=', request.env.uid), ('active', '!=', 'False'),
             ('accommodation_id', '=', accommodation_id.id)], limit=1)
        return {
            'uid': request.session.uid,
            'code': 200,
            'accommodation_id': accommodation_id.id,
            'cart': {
                'id': cart_id.id,
                'items': [{
                    'id': order_line.id,
                    'item_id': order_line.food_item_id.id,
                    'quantity': order_line.quantity,
                } for order_line in cart_id.food_order_line_ids],
            } if cart_id else {}
        }

    @http.route('/update_cart', type='json', website=True, auth='user')
    def update_cart(self, items, user):
        cart_id = request.env['website.cart'].sudo().browse(user['cart']['id']) if user.get('cart').get(
            'id') else request.env['website.cart'].sudo().search(
            [('user_id', '=', user.get('uid')), ('active', '!=', 'False'),
             ('accommodation_id', '=', user.get('accommodation_id'))], limit=1)
        if not cart_id:
            cart_id.create({
                'accommodation_id': user.get('accommodation_id'),
                'order_lines': [order_line.get('id') for order_line in items],
                'user_id': user.get('uid'),
            })
            return {
                'id': cart_id.id,
                'items': cart_id.food_item_ids.ids,
            }
        if not items:
            cart_id.food_item_ids = []
            return {
                'id': cart_id.id,
                'items': [],
            }
        cart_id.food_item_ids = [item.get('id') for item in items]
        return {
            'id': cart_id.id,
            'items': cart_id.food_item_ids.ids,
        }

    @http.route('/confirm_order', type='json', website=True, auth='user')
    def confirm_order(self, cart, user):
        return request.env['website.cart'].sudo().browse(cart['id']).confirm_order()