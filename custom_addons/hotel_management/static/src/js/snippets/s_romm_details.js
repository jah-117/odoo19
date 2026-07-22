/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class RoomDetails extends Interaction{
    static selector = '.s_room_details';

    async setup(){
        console.log('hello');
        // let rooms = await rpc("/hotel/room_details")
        this.rooms= await this.env.services.orm.call("hotel.room","get_room_details");
        this.startCarousal(this.rooms)
    }

    startCarousal(){
        var chunks = _.chunk(this.rooms,4)
        
    }

}

registry.category("public.interactions").add("hotel_management.room_details",RoomDetails)