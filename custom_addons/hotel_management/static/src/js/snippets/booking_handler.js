/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class HotelBookingForm extends Interaction {
    static selector = '#booking_form';

    setup() {
        this.updateRooms()
    }

    dynamicContent = {
        "#add_guest_line": {
            "t-on-click": (event) => this.addLine(event)
        },
        "#delete": {
            "t-on-click": (event) => this.deleteLine(event)
        },
        "#bed_type":{
            "t-on-change": (event) => this.updateRooms(event)
        }
    }
    addLine(event) {
        event.preventDefault();
        const line = `<tr>
            <td><input name="other_guest_name" id="other_guest_name" type="text" required="1"/></td>
            <td><input name="other_guest_age" id="other_guest_age" type="number" required="1"/></td>
            <td><select name="other_guest_gender" id="other_guest_gender">
                <option value="male">Male</option>
                <option value="female">Female</option>
            </select></td>
            <td><button id="delete">x</button></td>
        </tr>`;
        $("tbody").append(line);
    }
     deleteLine(event){
        event.preventDefault();
        event.currentTarget.parentElement.parentElement.remove();
    }
    updateRooms(event){
        $("#room_id").empty();
        let fetched = this.env.services.orm.call("hotel.room","get_available_rooms",[$("#bed_type").val()]);
        fetched.then((rooms)=>{
            for(let room in rooms){
                $("#room_id").append(`<option value="${rooms[room].room_id}">${rooms[room].room_no}</option>`);
            }
        })

    }
}

registry.category("public.interactions").add("hotel_management.booking_form", HotelBookingForm);