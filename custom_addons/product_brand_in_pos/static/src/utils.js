import {constructAttributeString} from "../../../../addons/point_of_sale/static/src/utils";

export function constructProductBrand(line){
    const attributeString = constructAttributeString(line);
    return attributeString
        ? `${line?.product_id?.brand} (${attributeString})`
        : `${line?.product_id?.brand}`;
}