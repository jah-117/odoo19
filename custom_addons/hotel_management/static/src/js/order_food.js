/** @odoo module **/
import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {renderToElement} from "@web/core/utils/render";

export class OrderFood extends Interaction {
    static selector = '.order-food';

    setup() {
        this.cart = [];
    }

    willStart() {
        // thisxs();
    }

    dynamicContent = {
        ".add_add": {
            "t-on-click": (event) => this.addadd(event)
        },
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

    addadd(event) {
        event.preventDefault();
        console.log(event)
    }

    loadFoodItems() {
        this.services.orm.call("food.items", "get_food_items").then((data) => {
            this.foodItems = data;
            this.updateFoodItems();
            this.loadCart()
        });
    }

    async loadCart() {
        this.user = await this.env.services.orm.rpc("/get_cart_data");
        if (this.user.code === 404) {
            window.alert(this.user.error);
            window.location.pathname = this.user.redirect_url;
        } else {
            if (this.user.cart !== false) {
                let right_split = document.querySelector('.right');
                for (let index = 0; index < this.user.cart.items.length; index++) {
                    let item = this.foodItems.find((item) => item.id === parseInt(this.user.cart.items[index].id))
                    if(item !== undefined) {
                        item.order_line_id = parseInt(this.user.cart.items[index].order_line_id)
                        item.quantity = parseInt(this.user.cart.items[index].quantity)
                        this.cart.push(item);
                        this.foodItems = this.foodItems.filter((item) => item.id !== parseInt(this.user.cart.items[index].id));
                    }
                }
                this.total = this.user.cart.total;
                document.querySelector('#total').innerHTML = `<p>Total Order amount: \$<span class="amount">${this.total}</span></p>`
                let cart_card = renderToElement('hotel_management.cart_card', {items: this.cart})
                document.querySelector('#cart').innerHTML = cart_card.innerHTML;
                right_split.style.display = 'block';

            }
            this.updateFoodItems();
        }
    }

    updateFoodItems() {
        if (!this.foodItems.length) {
            document.querySelector('#food_items').innerHTML = `<p>No food items found</p>`;
            return
        }
        let item_cards = renderToElement('hotel_management.item_card', {items: this.foodItems});
        document.querySelector('#food_items').innerHTML = item_cards.innerHTML
    }

    async updateCart(order_line_id=0) {
        let cart_card = renderToElement('hotel_management.cart_card', {items: this.cart})
        document.querySelector('#cart').innerHTML = cart_card.innerHTML;
        console.log(this.cart)
        this.user.cart = await this.env.services.orm.rpc('/update_cart', {items: this.cart, user: this.user,removed_order_line:order_line_id});
        this.total = this.user.cart.total;
        for (let index = 0; index < this.cart.length; index++) {
            this.cart[index].order_line_id = this.user.cart.items[index].order_line_id
        }
        document.querySelector('#total').innerHTML = `<p>Total Order amount: \$<span class="amount">${this.total}</span></p>`
    }

    addToCart(event) {
        event.preventDefault();
        let item_id= parseInt(event.currentTarget.attributes.getNamedItem('data-item_id').value);
        let item = this.foodItems.find((item) => item.id === item_id);
        item.quantity = 1;
        this.cart.push(item);
        this.foodItems = this.foodItems.filter((item) => item.id !== item_id);
        this.updateFoodItems();
        this.updateCart();
    }
    updateQuantity(event){
        let item_id = parseInt(event.currentTarget.getAttribute('data-item_id'));
        event.currentTarget.getAttribute('id') === 'increment'?
            this.cart.forEach((item,index, cart)=>{
                if(item.id === item_id){
                    cart[index].quantity = item.quantity+1;
                    cart[index].subtotal = item.price * cart[index].quantity;
                    this.updateCart()
                }
            }):
            this.cart.forEach((item,index,cart)=>{
                if (item.id === item_id) {
                    cart[index].quantity = item.quantity-1;
                    cart[index].subtotal = item.price * cart[index].quantity;
                    if(! item.quantity){
                        this.removeFromCart(false, item.id);
                    }
                    else{
                        this.updateCart();
                    }
                }
            });
     }
    removeFromCart(event =false, item_id=-1,) {
        event !== false ? event.preventDefault() : undefined;
        item_id = item_id !== -1 ? item_id : parseInt(event.currentTarget.attributes.getNamedItem('data-item_id').value);
        let item = this.cart.find((item) => item.id === item_id)
        this.cart = this.cart.filter((item) => item.id !== item_id);
        this.updateCart(item.order_line_id);
        item.order_line_id = 0;
        this.foodItems.push(item);
        this.updateFoodItems();
    }
    confirmOrder(event) {
        event.preventDefault();
        console.log('confirming')
        this.env.services.orm.rpc('/confirm_order', {cart: this.user.cart, user: this.user});
    }
}


registry.category("public.interactions").add("hotel_management.order_food", OrderFood)