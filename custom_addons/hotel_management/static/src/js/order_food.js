/** @odoo module **/

import { Interaction } from "@/web/public/interaction";
import { registry } from "@/web/core/registry";

export class OrderFood extends Interaction(){
    static selector = '.order-food'
    setup(){
        this.loadFoodItems()
    }


    async loadFoodItems(){
        this.foodItems = await this.env.services.orm.call('')
    }
}

registry.category("public.interactions").add("hotel_management.order_food",OrderFood)