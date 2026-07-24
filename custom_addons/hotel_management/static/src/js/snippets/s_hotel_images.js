/** @odoo module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class HotelImages extends Interaction{
    static selector = '.s_hotel_images';
    async setup(){
        this.items = await this.env.services.orm.call("res.config.settings","get_hotel_images");
        const hotel_images_snippet = document.querySelector('.images-section');
        if (this.items.number_of_images < 1){
            hotel_images_snippet.innerHTML = `<p>No images found<br/>Please add images in hotel management module settings<p/>`;
            return;
        }
        const carousalElement = renderToElement('hotel_management.hotel_images');
        let carousel_inner = carousalElement.querySelector('.carousel-inner');
        let carousel_indicators = carousalElement.querySelector('.carousel-indicators');
        let inner = '';
        let indicator = '';
        for(let i=0;i<this.items.number_of_images;i++){
            if (i === 0){
                inner =
`<div class="carousel-item active">
<img class="img img-fluid d-block mh-100 mw-100 mx-auto rounded object-fit-cover" src="${this.items.images[i]}" data-name="Image" data-index="${i}" alt=""/>
</div>`;
                indicator =
`<button type="button" data-bs-target="#hotel_image_carousel" data-bs-slide-to="${i}" background-image="url(${this.items.images[i]})" class="active" aria-label="Carousel indicator"/>`;
            } else{
                inner +=
`<div class="carousel-item">
                        <img class="img img-fluid d-block mh-100 mw-100 mx-auto rounded object-fit-cover" src="${this.items.images[i]}" data-name="Image" data-index="${i}" alt=""/>
                    </div>`;
                indicator +=
`<button type="button" background-image="url(${this.items.images[i]})"   data-bs-target="#hotel_image_carousel" data-bs-slide-to="${i}" aria-label="Carousel indicator"/>`;
            }
        }
        carousel_inner.innerHTML = inner;
        carousel_indicators.innerHTML = indicator;
        hotel_images_snippet.innerHTML = carousalElement.innerHTML;
    }
}
registry.category("public.interactions").add("hotel_management.hotel_images",HotelImages)