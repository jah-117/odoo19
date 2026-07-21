import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {patch} from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate = false) {
        super.validateOrder(isForceValidate)
        this.pos.data.call("stock.quant", "update_quantity_in_product", [[]])
    }

})