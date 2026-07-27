// /** @odoo module **/
// import { Interaction } from "@web/public/interaction";
// import { registry } from "@web/core/registry";
//
// export class ItemCard extends Interaction{
//     static selector = '.item-card';
//     setup(){
//         console.log('somethings')
//     }
//     dynamicContent = {
//         ".add_to_cart":{
//             "t-on-click":(event)=> this.addToCart(event)
//         }
//     }
//     addToCart(event){
//         console.log('ithanooo???')
//         event.preventDefault();
//         console.log(event);
//     }
// }
//
//
// registry.category("public.interactions").add("hotel_management.item_card",ItemCard)