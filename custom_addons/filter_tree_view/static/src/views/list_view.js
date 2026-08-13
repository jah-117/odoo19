/** @odoo-module **/
// import { ListController } from '@web/views/list/list_controller';
import {onWillStart} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {patch} from "@web/core/utils/patch";
import {ListRenderer} from "@web/views/list/list_renderer";
// export class SalesPersonFilter extends ListController {
//     setup(){
//         super.setup();
//         this.state = useState({salesPerson : null});
//         this.orm = useService("orm");
//         this.action = useService("action");
//         this.searchBar = SearchBar;
//         this.salesPersons =[];
//         onWillStart(async()=>{
//             this.salesPersons = await this.orm.searchRead("res.users",[],['id','name']);
//         });
//     }
//     async onChange(event){
//         this.state.salesPerson = parseInt(event.currentTarget.value);
//         await this.env.searchModel.clearQuery();
//         if(this.state.salesPerson) {
//             await this.env.searchModel.splitAndAddDomain(`[("user_id", "in", [${this.state.salesPerson}])]`);
//         }
//     }
// }
// registry.category('views').add('sale_person_filter', {
//     ...listView,
//      Controller:SalesPersonFilter
// });
// patch(ListController.prototype, {
//     setup(){
//         super.setup()
//         this.salesPersons = [];
//         this.orm = useService("orm");
//         onWillStart(async () => {
//             this.salesPersons = await this.orm.searchRead("res.users", [], ['id', 'name']);
//         });
//     },
//     async onChange(event) {
//         this.salesPerson = parseInt(event.currentTarget.value);
//         await this.env.searchModel.clearQuery();
//         if (this.salesPerson) {
//             await this.env.searchModel.splitAndAddDomain(`[("user_id", "in", [${this.salesPerson}])]`);
//         }
//     }
// });
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        onWillStart(async () => {
            if(this.env.searchModel.resModel==='crm.lead') {
                this.salesPersons = await this.orm.searchRead("res.users", [], ['id', 'name']);
            }
        });
    },
    async onChange(event) {
        this.salesPerson = parseInt(event.currentTarget.value);
        await this.env.searchModel.clearQuery();
        if (this.salesPerson) {
            await this.env.searchModel.splitAndAddDomain(`[("user_id", "in", [${this.salesPerson}])]`);
        }
    }
});
