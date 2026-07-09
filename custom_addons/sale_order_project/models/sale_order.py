from odoo import  fields,models,api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one('project.project',string="Project")
    available_project_ids = fields.Many2many('project.project',compute='_compute_available_projects',store=True)
    task_id = fields.Many2one('project.task',string="Task")
    create_invisible=fields.Boolean(string="Invisible",default=True,compute='_compute_create_invisible')
    subtask_ids = fields.Many2many('project.task',string="Tasks")
    subtask_count = fields.Integer(string="subtask count",default=0)

    @api.onchange('partner_id')
    def _compute_available_projects(self):
        self.project_id=False
        self.available_project_ids = self.env['project.project'].search([('partner_id','=',self.partner_id)])
    @api.depends('project_id','task_id','state')
    def _compute_create_invisible(self):
        if self.project_id and not self.task_id and self.state == 'sale':
            self.create_invisible = False
        else:
            self.create_invisible = True
    def create_task(self):
        self.task_id = self.env['project.task'].create({
            'name':f'SO/{self.name}-{self.partner_id.name}',
            'description':f'products:{'\n'.join([order_line.name for order_line in self.order_line])}',
            'project_id':self.project_id.id,
            'sale_order_id':self.id,
        })
        self.task_id.update({'user_ids': [fields.Command.link(id= self.user_id.id)]})
        priority={}
        orders = [order for order in self.order_line]
        orders.sort(key=lambda order: order.price_subtotal, reverse=True)
        for index in range(len(orders)):
            priority[f'{orders[index].id}'] = 3-index if 3-index>0 else 0
        self.task_id.update({'child_ids':[
            fields.Command.create({
                'name': f'{order.name}',
                'sale_order_id':self.id,
                'priority': str(priority.get(str(order.id),0)),
            }) for order in self.order_line
        ]})

        self.subtask_ids = self.task_id.child_ids
        self.subtask_count = len(self.subtask_ids)+1


    def action_view_tasks(self):
        print([('parent_id', '=', self.task_id.id)])
        return {
            'name':f'{self.name} taks',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            # 'domain': [('parent_id', '=', self.task_id.id)],
            'target': 'current',
            'view_mode':'list,form',
        }
        # return self.project_id.action_view_tasks()