/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import {  constructAttributeString } from "@point_of_sale/utils";


patch(PosOrderline.prototype,{
     get orderDisplayProductName() {
        return {
            name: this.product_id?.name,
            brand: this.product_id?.brand,
            attributeString: constructAttributeString(this),
        };
    }
});
