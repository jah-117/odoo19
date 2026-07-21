import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { onMounted } from "@odoo/owl";

patch(ProductScreen.prototype,{
    setup(){
        super.setup()
        onMounted( async () => {
            this.currentOrder.deselectOrderline();
            this.pos.openOpeningControl();
            // Call `reset` when the `onMounted` callback in `numberBuffer.use` is done.
            // We don't do this in the `mounted` lifecycle method because it is called before
            // the callbacks in `onMounted` hook.
            this.numberBuffer.reset();
            await this.refreshProduct();
        });
    },
     async refreshProduct(){
        this.pos.setSelectedCategory(0);
        const domain = [];

        const { limit_categories, iface_available_categ_ids } = this.pos.config;
        if (limit_categories && iface_available_categ_ids.length > 0) {
            const categIds = iface_available_categ_ids.map((categ) => categ.id);
            domain.push(["pos_categ_ids", "in", categIds]);
        }

        const results = await this.pos.loadNewProducts(domain, this.state.currentOffset, 30);
        return results["product.product"];
    }
})