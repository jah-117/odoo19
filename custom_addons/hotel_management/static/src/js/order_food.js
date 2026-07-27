/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement} from "@web/core/utils/render";

export class OrderFood extends Interaction {
    static selector = '.order-food';

    setup(){
        this.cart = [];
    }

    willStart(){
         this.loadFoodItems();
    }

    dynamicContent = {
        ".add_add":{
            "t-on-click":(event) => this.addadd(event)
        },
        ".add_to_cart":{
            "t-on-click": (event) => this.addToCart(event)
        },
        ".remove_from_cart":{
           "t-on-click" : (event) => this.removeFromCart(event)
        },
        ".confirm":{
            "t-on-click":(event) => this.confirmOrder(event)
        }
    }
    addadd(event){
        event.preventDefault();
        console.log(event)
    }
    loadFoodItems(){
        this.services.orm.call("food.items","get_food_items").then((data)=>{
            this.foodItems = data;
            this.updateFoodItems();
            this.loadCart()
        });

    }
    async loadCart(){
        this.user =  await this.env.services.orm.rpc("/get_cart_data");
        console.log(this.user)
        if(this.user.code === 404) {
            window.alert(this.user.error);
            window.location.pathname = this.user.redirect_url;
        } else {
            if(this.user.cart.items.length){
                let right_split = document.querySelector('.right');
                for(let index = 0; index < this.user.cart.items.length; index++){
                    this.addToCart( false, parseInt(this.user.cart.items[index]));
                }
                console.log(this.cart)
                right_split.style.display = 'block';
                this.updateFoodItems();
                this.updateCart();
            }
        }
    }
    updateFoodItems(){
        let item_cards = renderToElement('hotel_management.item_card',{items: this.foodItems});
        document.querySelector('#food_items').innerHTML = item_cards.innerHTML;
    }
    async updateCart(){
        let cart_card = renderToElement('hotel_management.cart_card',{items: this.cart})
        document.querySelector('#cart').innerHTML = cart_card.innerHTML;
        this.user.cart = await this.env.services.orm.rpc('/update_cart',{items:this.cart,user:this.user});
    }
    addToCart(event = false, item_id = -1){
        event !== false ? event.preventDefault() : undefined;
        item_id = item_id !== -1 ? item_id : event.currentTarget.attributes.getNamedItem('data-item_id').value;
        this.cart.push( ...(this.foodItems.filter((item)=> item.id === parseInt(item_id))));
        this.foodItems = this.foodItems.filter((item)=> item.id !== parseInt(item_id));
        this.updateFoodItems();
        item_id !== -1 ? this.updateCart() : undefined;
    }
    removeFromCart(event){
        let item_id = event.currentTarget.attributes.getNamedItem('data-item_id').value;
        this.foodItems.push(...(this.cart.filter((item)=>item.id === parseInt(item_id))));
        this.cart = this.cart.filter((item)=> item.id !== parseInt(item_id));
        this.updateFoodItems();
        this.updateCart();
    }
    confirmOrder(event){
        event.preventDefault();
        this.env.services.orm.rpc('/confirm_order',{cart: this.user.cart, user: this.user});
    }
}


registry.category("public.interactions").add("hotel_management.order_food",OrderFood)