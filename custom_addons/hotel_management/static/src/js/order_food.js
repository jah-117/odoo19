/** @odoo module **/
import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {renderToElement} from "@web/core/utils/render";

export class OrderFood extends Interaction {
    static selector = '.order-food';

    setup() {
        this.loadCart();
    }

    dynamicContent = {
        ".add_to_cart": {
            "t-on-click": (event) => this.addToCart(event)
        },
        ".remove_from_cart": {
            "t-on-click": (event) => this.removeFromCart(event)
        },
        ".count-btn": {
            "t-on-click": (event) => this.updateQuantity(event)
        },
        ".confirm-btn": {
            "t-on-click": (event) => this.confirmOrder(event)
        }
    }

    async loadCart() {
        this.user = await this.env.services.orm.rpc("/load_user_data");
        if (this.user.code === 404) {
            window.alert(this.user.error);
            window.location.pathname = this.user.redirect_url;
        }
    }

    async addToCart(event) {
        event.preventDefault();
        let cart = event.currentTarget.attributes.getNamedItem('data-cart_id');
        let res = await this.env.services.orm.rpc('/add_to_cart',{
            item_id:event.currentTarget.attributes.getNamedItem('data-item_id').value,
            cart_id:cart !== null ? cart.value : false,
            accommodation_id: this.user.accommodation_id,
        });
        if(parseInt(res.code)===400){
            window.alert(res.message)
        }
        window.location.reload();
    }
    async removeFromCart(event) {
        event.preventDefault();
        await this.env.services.orm.rpc('/remove_from_cart',{
            order_id:event.currentTarget.attributes.getNamedItem('data-order_id').value,
            cart_id:event.currentTarget.attributes.getNamedItem('data-cart_id').value,
        });
        window.location.reload();
    }

    async updateQuantity(event){
        let order_id = event.currentTarget.getAttribute('data-order_id')
        let res = await this.env.services.orm.rpc('/update_quantity',{
            order_id: order_id,
            is_increment: event.currentTarget.getAttribute('id') === 'increment',
        })
        if(parseInt(res.code) === 400){
            window.alert(res.message)
            window.location.reload();
            return
        }
        document.querySelector(`.quantity-${order_id}`).value = res.quantity;
        document.querySelector(`.order-line-${order_id}`).innerHTML = `${res.subtotal}$`
        document.querySelector(`.cart-total`).innerHTML = `${res.total} $`;
     }
    async confirmOrder(event) {
        event.preventDefault();
        let res = await this.env.services.orm.rpc('/confirm_order', {
            cart_id:event.currentTarget.attributes.getNamedItem('data-cart_id').value,
        });
        console.log(res);
        window.alert(res.message);
        window.location.replace('/');

    }
}


registry.category("public.interactions").add("hotel_management.order_food", OrderFood)