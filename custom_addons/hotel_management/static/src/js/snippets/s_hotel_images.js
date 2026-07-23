/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class HotelImages extends Interaction{
    static selector = '.s_hotel_images';
    async setup(){
        this.images=[
            "/hotel_management/static/src/img/hotel_1.jpg",
            "/hotel_management/static/src/img/hotel_2.jpg",
            "/hotel_management/static/src/img/hotel_3.jpg",
            "/hotel_management/static/src/img/hotel_4.jpg",
            "/hotel_management/static/src/img/hotel_5.jpg",
        ]
        const carousalElement = renderToElement('hotel_management.hotel_images',{images:this.images})
        document.querySelector('.images-section').innerHTML = carousalElement.innerHTML
    }
}
registry.category("public.interactions").add("hotel_management.hotel_images",HotelImages)