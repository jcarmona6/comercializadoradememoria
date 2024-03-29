from odoo import fields, models, api, _
from odoo.exceptions import UserError

class claim_process_wizard(models.TransientModel):
    _name = 'claim.process.wizard'
    _description = 'Wizard to process claim lines'

    claim_line_id = fields.Many2one('claim.line.ept', "Claim Line")
    # ticket_id = fields.Many2one('helpdesk.ticket', "Ticket")
    picking_id = fields.Many2one('stock.picking')
    product_id = fields.Many2one('product.product', "Product to be Replace")
    quantity = fields.Float("Quantity")
    is_create_invoice = fields.Boolean('Create Invoice')
    reject_message_id = fields.Many2one("claim.reject.message", "Reject Reason")
    send_goods_back = fields.Boolean("Send Goods Back to Customer")
    hide = fields.Selection([('true', 'true'), ('false', 'false')], default='true')
    state = fields.Char()
    is_visible_goods_back = fields.Boolean()

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.id == self._context.get('product_id'):
            self.hide = 'true'
        else:
            self.hide = 'false'

    @api.model
    def default_get(self, default_fields):
        """
        This method used to set a default value in the wizard.
        Add help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        res = super(claim_process_wizard, self).default_get(default_fields)
        if self._context.get('active_model') == 'crm.claim.ept':
            claim = self.env[self._context.get('active_model')].search(
                    [('id', '=', self._context.get('active_id'))])
            res['picking_id'] = claim.return_picking_id and claim.return_picking_id.id or False
            if claim.return_picking_id:
                if claim.return_picking_id.state == 'cancel':
                    res['is_visible_goods_back'] = False
                else:
                    res['is_visible_goods_back'] = True
        else:
            line = self.env['claim.line.ept'].search([('id', '=', self._context.get('active_id'))])
            res['claim_line_id'] = line.id
            res['state'] = line.claim_id.state if line.claim_id else line.ticket_id.state
            res['product_id'] = line.to_be_replace_product_id.id or line.product_id.id
            res['quantity'] = line.to_be_replace_quantity or line.quantity
            res['is_create_invoice'] = line.is_create_invoice
        return res

    def process_refund(self):
        if not self.claim_line_id:
            return False
        if self.claim_line_id.product_id == self.product_id:
            raise UserError(_("Please replace the product with other product, it seems like you replace with the same product."))
        self.claim_line_id.write({'to_be_replace_product_id':self.product_id.id,
                                  'to_be_replace_quantity':self.quantity,
                                  'is_create_invoice':self.is_create_invoice})
        return True

    def reject_claim(self):
        """
        This method used to reject claim.
        Add help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        claim_line_ids = self.env['claim.line.ept'].search(
                [('id', 'in', self.env.context.get('claim_lines'))])
        if not claim_line_ids:
            raise UserError('Claim Lines not found')
        claim = claim_line_ids[0].claim_id
        if claim.return_picking_id and claim.return_picking_id.state not in ['done', 'cancel']:
            raise UserError("Please first process Return Picking Order.")
        claim.write({'reject_message_id':self.reject_message_id.id, 'state':'reject'})
        if self.send_goods_back:
            claim.create_return_picking(claim_line_ids)
        #claim.action_rma_send_email()
        return True

    # def create_return_delivery(self):
    #     repair_orders = self.env['repair.order'].browse(self._context.get('active_ids'))
    #     for repair_order in repair_orders:
    #         if re
    #     return True
