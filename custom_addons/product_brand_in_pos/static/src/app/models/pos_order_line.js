/** @odoo-module **/
import { PosOrderline } from "@point_of_sale/static/src/app/models/pos_order_line"
import {constructProductBrand} from "../../utils";

export class PosOrderLine extends PosOrderline {

    setProductBrand(){
        this.product_brand = constructProductBrand(this)
    }
}