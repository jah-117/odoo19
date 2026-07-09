import { Orderline } from "@point_of_sale/static/src/app/components/orderline/orderline"
import { patch } from "@web/core/utils/patch";

patch(Orderline,
    {get lineScreenValues(){
        const line = this.line;

        // Prevent rendering if the line is not yet linked to an order
        // this can happen during related models connections
        if (!line.order_id) {
            return {};
        }

        const imageUrl = line.product_id?.getImageUrl();
        const basic = this.props.basic_receipt;
        const unitPart = line.getQuantityStr().unitPart;
        const decimalPart = line.getQuantityStr().decimalPart;
        const decimalPoint = line.getQuantityStr().decimalPoint;
        const discount = line.getDiscountStr();
        const mode = this.props.mode;
        const attributeStr = line.orderDisplayProductName.attributeString;
        const taxGroup = this.line.taxGroupLabels;
        const showPrice =
            !basic &&
            line.getQuantityStr() != 1 &&
            (mode === "receipt" || (line.price_type !== "original" && !line.combo_parent_id));
        const priceUnit = `${line.currencyDisplayPriceUnit} / ${
            line.product_id?.uom_id?.name || ""
        }`;
        return {
            name: mode === "receipt" ? line.full_product_name : line.orderDisplayProductName.name,
            brand: line.product_brand,
            attributeString:
                ["display", "split"].includes(mode) && attributeStr && `- ${attributeStr}`,
            internalNote: mode === "display" && line.note && JSON.parse(this.line.note || "[]"),
            isReceipt: mode === "receipt",
            isDisplay: mode === "display",
            discount: !basic && discount && discount !== "0" && !line.combo_parent_id && discount,
            noDiscountPrice: formatCurrency(line.displayPriceNoDiscount, line.currency.id),
            displayPriceUnit: showPrice && line.price !== 0 && priceUnit,
            unitPart: unitPart,
            decimalPart: decimalPart && `${decimalPoint}${decimalPart}`,
            productImage: this.props.showImage && imageUrl,
            taxGroup: this.props.showTaxGroup && taxGroup,
            price: !basic && !line.combo_parent_id && this.line.currencyDisplayPrice,
            lotLines: line.product_id.tracking !== "none" && (line.packLotLines || []),
        };}
});