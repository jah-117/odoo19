from odoo import http, fields
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
                    'order_line_id': order_line.id,
                    'id': order_line.food_item_id.id,
                    'quantity': order_line.quantity,
                    'subtotal': order_line.subtotal,
                } for order_line in cart_id.food_order_line_ids],
                'total':cart_id.total,
            } if cart_id else False

        }

    @http.route('/update_cart', type='json', website=True, auth='user')
    def update_cart(self, items, user,removed_order_line):
        cart_id = request.env['website.cart'].sudo().browse(user['cart']['id']) if user.get('cart') else request.env[
            'website.cart'].sudo().search(
            [('user_id', '=', user.get('uid')), ('active', '!=', 'False'),
             ('accommodation_id', '=', user.get('accommodation_id'))], limit=1)
        if not cart_id:
            cart_id= request.env['website.cart'].sudo().create({
                'accommodation_id': user.get('accommodation_id'),
                'user_id': user.get('uid'),
            })
        total = 0
        if removed_order_line:
            request.env['food.order.lines'].sudo().browse(int(removed_order_line)).unlink()
            cart_id.total =sum([float(order_line.get('quantity')) * float(order_line.get('price')) for order_line in items])
            return {
                'id': cart_id.id,
                'items': [{
                    'order_line_id': order_line.id,
                    'id': order_line.food_item_id.id,
                    'quantity': order_line.quantity,
                    'subtotal': order_line.subtotal,
                } for order_line in cart_id.food_order_line_ids],
                'total': cart_id.total,
            }
        for order_line in items:
            total += float(order_line.get('quantity'))*float(order_line.get('price'))
            if order_line.get('order_line_id'):
                request.env['food.order.lines'].sudo().browse(int(order_line.get('order_line_id'))).update({
                    'quantity': order_line.get('quantity'),
                    'subtotal': order_line.get('subtotal'),
                })
            else:
                cart_id.update({
                    'food_order_line_ids': [
                        fields.Command.create({
                            'food_item_id': request.env['food.order.lines'].sudo().browse(int(order_line.get('id'))).id,
                            'quantity': order_line.get('quantity'),
                            'subtotal': order_line.get('subtotal'),
                        })
                    ]
                })
        cart_id.total = total
        return {
            'id': cart_id.id,
            'items': [{
                    'order_line_id': order_line.id,
                    'id': order_line.food_item_id.id,
                    'quantity': order_line.quantity,
                    'subtotal': order_line.subtotal,
                } for order_line in cart_id.food_order_line_ids],
            'total': cart_id.total,
        }

    @http.route('/confirm_order', type='json', website=True, auth='user')
    def confirm_order(self, cart, user):
        return request.env['website.cart'].sudo().browse(int(cart['id'])).confirm_order()
