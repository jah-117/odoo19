/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class OrderFood extends Interaction {
    static selector = '#order-food';

    setup(){
        this.loadFoodItems();
    }

    loadFoodItems(){
        this.env.services.orm.call("food.items","get_food_items").then((data)=>{
            console.log(data)
            this.foodItems = data
            console.log(this.foodItems)
        });
    }
}

registry.category("public.interactions").add("hotel_management.order_food",OrderFood)