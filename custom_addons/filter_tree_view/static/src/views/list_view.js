/** @odoo-module **/
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { useState } from "@odoo/owl";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useService } from "@web/core/utils/hooks";
export class SalesPersonFilter extends ListController {
    setup(){
        super.setup();
        this.state = useState({salesPerson : null});
        this.orm = useService("orm");
        this.action = useService("action");
        this.searchBar = SearchBar
        this.salesPersons =[]
        this.fetchSalesPersons();
    }

    async fetchSalesPersons(){
       this.salesPersons = await this.orm.searchRead("res.users",[],['id','name']);
    }
    async onChange(event){
        this.state.salesPerson = event.currentTarget.value;
        // this.model.env.searchModel.domain =[
        //     // ...this.model.env.searchModel.domain,
        //     // ["user_id",'=',this.state.salesPerson]
        // ]
        console.log(this.searchBar.set)
        console.log(ListController.components.SearchBar)
        console.log(this.model.env.searchModel.domain);
    }
}
registry.category('views').add('sale_person_filter', {
    ...listView,
     Controller:SalesPersonFilter
});
