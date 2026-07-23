/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class RoomDetails extends Interaction{
    static selector = '.s_room_details';
    async setup(){
        this.rooms = await this.env.services.orm.call("hotel.room","get_room_details");
        const carousalElement = renderToElement('hotel_management.carousal_snippet',{rooms :this.rooms})
        document.querySelector('.display_carousal').innerHTML = carousalElement.innerHTML
    }
}
registry.category("public.interactions").add("hotel_management.room_details",RoomDetails)