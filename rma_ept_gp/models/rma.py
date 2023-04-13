# Copyright 2015 ADHOC SA  (http://www.adhoc.com.ar)
# Copyright 2015-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models,_
from odoo.exceptions import UserError


class claim_process_wizard(models.TransientModel):
    _inherit = 'claim.process.wizard'
    _description = 'Wizard to process claim lines'

    def process_refund(self):
        if not self.claim_line_id:
            return False
        #if self.claim_line_id.product_id == self.product_id:
        #    raise UserError(_("Please replace the product with other product, it seems like you replace with the same product."))
        self.claim_line_id.write({'to_be_replace_product_id':self.product_id.id,
                                  'to_be_replace_quantity':self.quantity,
                                  'is_create_invoice':self.is_create_invoice})
        return True

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.hide = 'false'


class CRMClaimLine(models.Model):
    _inherit = 'claim.line.ept'
    _description = 'CRM Claim Line'

    unit_price = fields.Float('Unit Price')
    subtotal = fields.Float('Sub Total', compute = 'compute_subtotal', store = False)


    @api.depends('unit_price', 'quantity')
    def compute_subtotal(self):
        for rec in self:
            rec.subtotal = 0
            if rec.unit_price and rec.quantity:
                rec.subtotal = rec.unit_price * rec.quantity

    @api.onchange('quantity', 'unit_price')
    def on_quantity(self):
        for rec in self:
            rec.subtotal = 0
            if rec.unit_price and rec.quantity:
                rec.subtotal = rec.unit_price * rec.quantity

    @api.constrains('quantity')
    def check_qty(self):
        if self.claim_id.external_reference:
            return False
        for line in self:
            if line.quantity < 0:
                raise UserError(_('Quantity must be positive number'))
            elif line.quantity > line.move_id.quantity_done:
                raise UserError(_('Quantity must be less than or equal to the delivered quantity'))


class CrmClaimEptReferences(models.Model):
    _name = "crm.claim.ept.references"
    _description = "crm.claim.ept.references"
    name = fields.Char()
    rma_id = fields.Many2one('crm.claim.ept')

    def name_get(self):
        return [(rec.id, rec.name) for rec in self]


class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"


    external_reference = fields.Char('External Reference')
    journal_id = fields.Many2one('account.journal', 'Journal')
    customer_reference_ids = fields.One2many('crm.claim.ept.references', 'rma_id')
    operation_type = fields.Many2one('stock.picking.type')
    return_item_barcode = fields.Char('Return Item Serial')
    receipt_number = fields.Char('Receipt Number')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    sale_order_delivery_id = fields.Many2one('sale.order', 'Sale Order Delivery')


    def get_serial_numbers_from_order(self, order):
        if not order:
            return False

        delivery_ids = order.picking_ids.filtered(lambda r: r.state in ['done'])
        lot_ids = []
        for delivery in delivery_ids:
            if delivery.move_lines and \
                    delivery.move_lines.move_line_ids.lot_id:
                lot_ids.append(delivery.move_lines.move_line_ids.lot_id.ids[0])

        return lot_ids or False

    @api.depends('claim_line_ids')
    def _compute_lot_ids(self):
        res = super(CrmClaimEpt, self)._compute_lot_ids()
        for claim_id in self:
            if claim_id.external_reference:
                order = self.env['sale.order'].search([('name', '=', claim_id.external_reference.split()[0])])
                if order:
                    claim_id.claim_lot_ids = self.get_serial_numbers_from_order(order)



    @api.onchange('picking_id')
    def onchange_picking_id(self):
        """
        This method is used to set default values in the RMA base on delivery changes.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        claim_lines = []
        crm_calim_line_obj = self.env['claim.line.ept']
        # lot_serial_obj = self.env['lot.serial.number.ept']
        if self.picking_id:
            self.partner_id = self.picking_id.partner_id.id
            self.partner_phone = self.picking_id.partner_id.phone
            self.email_from = self.picking_id.partner_id.email
            self.sale_id = self.picking_id.sale_id.id
            self.partner_delivery_id = self.picking_id.sale_id and self.picking_id.sale_id.partner_shipping_id and self.picking_id.sale_id.partner_shipping_id.id or self.picking_id.rma_sale_id and self.picking_id.rma_sale_id.partner_shipping_id and self.picking_id.rma_sale_id.partner_shipping_id.id or False
            for move_id in self.picking_id.move_lines:
                previous_claimline_ids = crm_calim_line_obj.search(
                    [('move_id', '=', move_id.id), ('product_id', '=', move_id.product_id.id)])



                if previous_claimline_ids:
                    returned_qty = 0
                    for line_id in previous_claimline_ids:
                        returned_qty += line_id.quantity

                    if returned_qty < move_id.quantity_done:
                        qty = move_id.quantity_done - returned_qty
                        if qty > 0:
                            sale_order_line = self.sale_id.order_line.filtered(
                                lambda r: r.product_id == move_id.product_id and r.product_uom_qty == qty)

                            if len( sale_order_line ) > 1:
                                sale_order_line = sale_order_line[ 0 ]

                            claim_lines.append((0, 0, {'product_id': move_id.product_id.id,
                                                       'quantity': qty,
                                                       'move_id': move_id.id,
                                                       'unit_price' : sale_order_line.price_unit if sale_order_line else False}))

                else:
                    if move_id.quantity_done > 0:
                        sale_order_line = self.sale_id.order_line.filtered(
                            lambda r: r.product_id == move_id.product_id and r.product_uom_qty == move_id.quantity_done)

                        if len(sale_order_line) > 1:
                            sale_order_line = sale_order_line[0]

                        claim_lines.append((0, 0, {'product_id': move_id.product_id.id,
                                                   'quantity': move_id.quantity_done,
                                                   'move_id': move_id.id,
                                                   'unit_price' : sale_order_line.price_unit if sale_order_line else False
                                                   }))
            self.claim_line_ids = [(5, 0, 0)] + claim_lines


    @api.onchange('external_reference', 'partner_id')
    def _onchange_external_reference(self):
        for rec in self:
            if rec.external_reference:
                external_references = rec.external_reference.split(',')
                order_ids = self.env['sale.order'].search([('name', 'in', external_references), ('partner_id', '=', rec.partner_id.id)])
                customer_references = order_ids.mapped('client_order_ref')
                customer_reference_ids = []
                for ref in customer_references:
                    if ref:
                        client_order_refs = ref.split(',')
                        for client_ref in client_order_refs:
                            if not rec.customer_reference_ids.filtered(lambda l: l.name == client_ref):
                                customer_reference_ids.append((0,0,{'name': client_ref}))
                if customer_reference_ids:
                    rec.customer_reference_ids = customer_reference_ids

    def process_claim(self):
        res = super(CrmClaimEpt, self).process_claim()
        return res


    def create_so(self, lines):
        """
        This method used to create a sale order.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        if not self.picking_id and not self.warehouse_id:
            raise UserError('The warehouse is required for this operation')

        sale_order = self.env['sale.order']
        order_vals = {
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id if self.warehouse_id else self.sale_id.warehouse_id.id,
        }
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_id()
        order_vals = sale_order._convert_to_write(
            {name: new_record[name] for name in new_record._cache})
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_shipping_id()
        order_vals = sale_order._convert_to_write(
            {name: new_record[name] for name in new_record._cache})
        order_vals.update({
            'state': 'draft',
            'team_id': self.section_id.id,
            'client_order_ref': self.name,
        })
        so = sale_order.create(order_vals)
        self.new_sale_id = so.id
        for line in lines:
            sale_order_line = self.env['sale.order.line']
            order_line = {
                'order_id': so.id,
                'product_id': line.to_be_replace_product_id.id,
                'company_id': self.company_id.id,
                'name': line.to_be_replace_product_id.name
            }
            new_order_line = sale_order_line.new(order_line)
            new_order_line.product_id_change()
            order_line = sale_order_line._convert_to_write(
                {name: new_order_line[name] for name in new_order_line._cache})
            order_line.update({
                'product_uom_qty': line.to_be_replace_quantity,
                'state': 'draft',
            })
            sale_order_line.create(order_line)
        self.write({'new_sale_id': so.id})
        return True

    def create_refund(self, lines):
        if self.picking_id:
            refund_obj = self.env['account.move.reversal']
            invoice_obj = self.env['account.move']
            if not self.sale_id.invoice_ids:
                message = _(
                    "The invoice was not created for Order : <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>") % (
                              self.sale_id.id, self.sale_id.name)
                self.message_post(body=message)
                return False
            refund_invoice_ids = {}
            refund_invoice_ids_rec = []
            product_process_dict = {}
            is_create_refund = False
            for line in lines:
                if self.is_rma_without_incoming:
                    if line.id not in product_process_dict:
                        if line.to_be_replace_quantity <= 0:
                            product_process_dict.update({line.id: {'total_qty': line.quantity,
                                                                   'invoice_line_ids': {}}})
                        else:
                            product_process_dict.update(
                                {line.id: {'total_qty': line.to_be_replace_quantity,
                                           'invoice_line_ids': {}}})
                if line.id not in product_process_dict:
                    product_process_dict.update(
                        {line.id: {'total_qty': line.return_qty, 'invoice_line_ids': {}}})
                for invoice_line in line.move_id.sale_line_id.invoice_lines:
                    if invoice_line.move_id.state != 'posted' or invoice_line.move_id.move_type != 'out_invoice':
                        message = _("The invoice was not posted. Please check invoice")
                        self.message_post(body=message)
                        continue
                    is_create_refund = True
                    if product_process_dict.get(line.id).get('process_qty',
                                                             0) < product_process_dict.get(line.id).get(
                        'total_qty', 0):
                        if product_process_dict.get(line.id).get('process_qty',
                                                                 0) + invoice_line.quantity < product_process_dict.get(
                            line.id).get('total_qty', 0):
                            process_qty = invoice_line.quantity
                            product_process_dict.get(line.id).update(
                                {'process_qty': product_process_dict.get(line.id).get(
                                    'process_qty', 0) + invoice_line.quantity})
                        else:
                            process_qty = product_process_dict.get(line.id).get('total_qty',
                                                                                0) - product_process_dict.get(
                                line.id).get('process_qty', 0)
                            product_process_dict.get(line.id).update(
                                {'process_qty': product_process_dict.get(line.id).get('total_qty',
                                                                                      0)})
                        product_process_dict.get(line.id).get('invoice_line_ids').update(
                            {invoice_line.id: process_qty, 'invoice_id': invoice_line.move_id.id})
                        if refund_invoice_ids.get(invoice_line.move_id.id):
                            refund_invoice_ids.get(invoice_line.move_id.id).append(
                                {invoice_line.product_id.id: process_qty,
                                 'price': line.unit_price or line.move_id.sale_line_id.price_unit,
                                 'tax_id': line.move_id.sale_line_id.tax_id.ids,
                                 'discount': line.move_id.sale_line_id.discount
                                 })
                        else:
                            refund_invoice_ids.update({invoice_line.move_id.id: [
                                {invoice_line.product_id.id: process_qty,
                                 'price': line.unit_price or line.move_id.sale_line_id.price_unit,
                                 'tax_id': line.move_id.sale_line_id.tax_id.ids,
                                 'discount': line.move_id.sale_line_id.discount
                                 }]})
            if not is_create_refund:
                return False
            # if self.is_rma_without_incoming and not refund_invoice_ids:
            #     message = (_("The refund invoice is not created. The claim is no incoming shipment."))
            #     self.message_post(body=message)

            for invoice_id, lines in refund_invoice_ids.items():
                invoice = invoice_obj.browse(invoice_id)
                refund_process = refund_obj.create({
                    'move_ids': [(6, 0, [invoice_id])],
                    'reason': 'Refund Process of Claim - ' + self.name,
                    'journal_id': self.journal_id.id,
                })
                refund = refund_process.reverse_moves()
                refund_invoice = refund and refund.get('res_id') and invoice_obj.browse(
                    refund.get('res_id'))
                refund_invoice.write({
                    'invoice_origin': invoice.name,
                    'claim_id': self.id
                })
                if not refund_invoice:
                    continue
                refund_invoice and refund_invoice.invoice_line_ids and \
                refund_invoice.invoice_line_ids.with_context(check_move_validity=False).unlink()
                for line in lines:
                    if not list(line.keys()) or not list(line.values()):
                        continue
                    price = line.get('price')
                    del line['price']
                    product_id = self.env['product.product'].browse(list(line.keys())[0])
                    if not product_id:
                        continue
                    line_vals = self.env['account.move.line'].new({'product_id': product_id.id,
                                                                   'name': product_id.name,
                                                                   'move_id': refund_invoice.id,
                                                                   'discount': line.get('discount') or 0
                                                                   # 'account_id': invoice.account_id.id
                                                                   })
                    line_vals._onchange_product_id()
                    line_vals = line_vals._convert_to_write(
                        {name: line_vals[name] for name in line_vals._cache})
                    if line.get('tax_id'):
                        line_vals.update({'tax_ids': [(6, 0, line.get('tax_id'))]})
                    else:
                        line_vals.update({'tax_ids': [(6, 0, [])]})
                    line_vals.update({'quantity': list(line.values())[0], 'price_unit': price})
                    self.env['account.move.line'].with_context(check_move_validity=False).create(
                        line_vals)
                refund_invoice.with_context(check_move_validity=False)._recompute_dynamic_lines(
                    recompute_all_taxes=True)
                refund_invoice_ids_rec.append(refund_invoice.id)
            refund_invoice_ids_rec and self.write(
                {'refund_invoice_ids': [(6, 0, refund_invoice_ids_rec)]})
        else:
            account_move_model = self.env['account.move']
            invoice_line_ids = []
            for line in lines:
                if line.claim_type == 'refund' or line.claim_type == 'replace_other_product' or line.claim_type == 'replace_same_produt':
                    invoice_line_ids.append((0,0,{
                        'quantity': line.quantity,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_id.uom_id.id,
                        'company_id': self.company_id.id,
                        'price_unit' : line.unit_price
                    }))

            if invoice_line_ids:
                if not self.journal_id:
                    raise UserError('Please set the correct journal')

                refund_obj = account_move_model.with_context(active_model = 'crm.claim.ept', active_id = self.id).create({
                    'journal_id' : self.journal_id.id if self.journal_id else False,
                    'partner_id' : self.partner_id.id,
                    'ref' : self.code +' '+ self.external_reference,
                    'invoice_line_ids' : invoice_line_ids,
                    'move_type' : 'out_refund',
                    'company_id' : self.company_id.id
                })
                refunds_created = []
                for ref in self.refund_invoice_ids:
                    refunds_created.append( ref.id )

                refunds_created.append( refund_obj.id )

                self.write({'refund_invoice_ids': [(6, 0, refunds_created)]})

    def create_do(self, lines):
        if self.picking_id:
            return super(CrmClaimEpt, self).create_do(lines)
        else:
            do = self.env['stock.picking'].create(
                {'partner_id': self.partner_id.id, 'location_id': self.operation_type.default_location_dest_id.id,
                 'location_dest_id': self.operation_type.default_location_src_id.id,
                 'picking_type_id': self.operation_type.id, 'origin': self.name,
                 "rma_sale_id": self.sale_id.id})
            for line in lines:
                self.env['stock.move'].create({
                    'location_id': self.operation_type.default_location_dest_id.id,
                    'location_dest_id': self.operation_type.default_location_src_id.id,
                    'product_uom_qty': line.to_be_replace_quantity or line.quantity,
                    'name': line.to_be_replace_product_id.name or line.product_id.name,
                    'product_id': line.to_be_replace_product_id.id or line.product_id.id,
                    'state': 'draft',
                    'picking_id': do.id,
                    'product_uom': line.to_be_replace_product_id.uom_id.id or line.product_id.uom_id.id,
                    'company_id': self.company_id.id,
                    'sale_line_id': line.move_id.sale_line_id.id if line.move_id.sale_line_id else False
                })

            self.write({'to_return_picking_ids': [(4, do.id)]})
            self.sale_id.write({'picking_ids': [(4, do.id)]})
            do.action_assign()
            return True

    def get_so(self):
        for record in self:
            if record.picking_id:
                record.sale_id = record.picking_id.sale_id.id

            if not record.sale_id:
                record.sale_id = False

    def approve_claim(self):
        """
        This method used to approve the RMA. It will create a return picking base on the RMA configuration.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        if self.picking_id:
            return super(CrmClaimEpt, self).approve_claim()

        crm_calim_line_obj = self.env['claim.line.ept']
        processed_product_list = []
        if len(self.claim_line_ids) <= 0:
            raise UserError(_("Please set return products."))
        repair_line = []
        total_qty = 0
        repair_line = []
        for line in self.claim_line_ids:
            if line.quantity <= 0 or not line.rma_reason_id:
                raise UserError(_("Please set Return Quantity and Reason for all products."))
            # if line.product_id.tracking in ['serial', 'lot']:
            # if line.product_id.tracking in ['serial', 'lot']:
            #     if line.product_id.tracking == 'serial' and len(line.serial_lot_ids) != \
            #             line.quantity:
            #         raise UserError(_(
            #             "Please set Serial number for product: '%s'." % (
            #                 line.product_id.name)))
            #     elif line.product_id.tracking == 'lot' and len(line.serial_lot_ids) != 1:
            #         raise UserError(_(
            #             "Please set Lot number for product: '%s'." % (line.product_id.name)))
            if line.claim_type == 'repair':
                repair_line.append(line)

            if line.move_id:
                moves = line.search([('move_id', '=', line.move_id.id)])
                for m in moves:
                    if m.claim_id.state in ['process', 'approve', 'close']:
                        total_qty += m.quantity
                if total_qty >= line.move_id.quantity_done:
                    processed_product_list.append(line.product_id.name)
            for move_id in self.picking_id.move_lines:
                previous_claimline_ids = crm_calim_line_obj.search(
                    [('move_id', '=', move_id.id), ('product_id', '=', move_id.product_id.id),
                     ('claim_id.state', '=', 'close')])
                if previous_claimline_ids:
                    returned_qty = 0
                    for line_id in previous_claimline_ids:
                        returned_qty += line_id.quantity

                    if returned_qty < move_id.quantity_done:
                        qty = move_id.quantity_done - returned_qty
                        if line.quantity > qty:
                            raise UserError(_(
                                "You have already one time process RMA. So You need to check Product Qty"))

        if processed_product_list and not self.external_reference:
            raise UserError(_('%s Product\'s delivered quantites were already processed for RMA' % (
                ", ".join(processed_product_list))))
        self.write({'state': 'approve'})
        if self.is_rma_without_incoming:
            # Below code comment becuase when the select repair order in claim line that time we
            # create default return picking in the claim we need we can remove the comment on
            # date 19_02_2020 Addedby Haresh Mori
            # repair_line and self.create_return_picking_for_repair(repair_line)
            # self.return_picking_id and self.return_picking_id.write({'claim_id':self.id})
            self.write({'state': 'process'})
        else:
            self.create_return_picking()
            self.return_picking_id and self.return_picking_id.write({'claim_id': self.id})
        #self.action_rma_send_email()

        if not self.picking_id and self.external_reference and self.state == 'approve':
            self.write({'state': 'process'})

        return True


    @api.constrains('picking_id')
    def check_picking_id(self):
        """
        This method used check picking is created from sale order if picking is not created from
        the sale order it will generate a UserError message.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        for record in self:
            if not record.sale_id:
                if not record.picking_id.rma_sale_id and not self.external_reference:
                    raise UserError(
                        "Sale Order not found in delivery, Please select valid delivery with sale order")


    def create_return_picking(self, claim_lines=False):
        """
        This method used to create a return picking, when the approve button clicks on the RMA.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        if self.picking_id:
            return super(CrmClaimEpt, self).create_return_picking(claim_lines)


        stock_picking_obj = self.env['stock.picking']
        stock_move_line_obj = self.env['stock.move.line']

        if self.external_reference:
            lines = claim_lines or self.claim_line_ids
            new_picking_obj = stock_picking_obj.create({
                'partner_id' : self.partner_id.id,
                'picking_type_id' : self.operation_type.id,
                'location_dest_id' :  self.operation_type.default_location_dest_id.id,
                'location_id' :  self.operation_type.default_location_src_id.id,
                'origin' : self.external_reference,
                'company_id': self.company_id.id,
            })
            new_picking_id = new_picking_obj.id
            for line in lines:
                self.env['stock.move'].create({
                    'location_id': self.operation_type.default_location_src_id.id,
                    'location_dest_id': self.operation_type.default_location_dest_id.id,
                    'product_uom_qty': line.quantity,
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'state': 'draft',
                    'picking_id': new_picking_obj.id,
                    'product_uom': line.product_id.uom_id.id,
                    'company_id': self.company_id.id,
                })

            pick_type_id = self.operation_type
            self.return_picking_id = new_picking_id
        else:
            location_id = self.location_id.id
            return_picking_wizard = self.env['stock.return.picking'].create({
            })
            if location_id and not claim_lines:
                return_picking_wizard.write({'location_id': location_id})
            return_lines = []
            lines = claim_lines or self.claim_line_ids
            for line in lines:
                move_id = self.env['stock.move'].search([('product_id', '=', line.product_id.id), (
                    'picking_id', '=',
                    self.return_picking_id.id if claim_lines else self.picking_id.id),
                                                         ('sale_line_id', '=',
                                                          line.move_id.sale_line_id.id)])
                return_line = self.env['stock.return.picking.line'].create(
                    {'product_id': line.product_id.id, 'quantity': line.quantity,
                     'wizard_id': return_picking_wizard.id,
                     'move_id': move_id.id})
                return_lines.append(return_line.id)

            return_picking_wizard.write({'product_return_moves': [(6, 0, return_lines)]})
            new_picking_id, pick_type_id = return_picking_wizard._create_returns()


            if claim_lines:
                self.write({'to_return_picking_ids': [(4, new_picking_id)]})
            else:
                self.return_picking_id = new_picking_id
                # Below line Addedby haresh Mori on date 6/1/2020 to set lot/serial number on the
                # stock move line
                for claim_line in self.claim_line_ids:
                    for stock_move in self.return_picking_id.move_lines:
                        if claim_line.product_id == stock_move.product_id:
                            move_line_vals = {
                                'move_id': stock_move.id,
                                'location_id': stock_move.location_id.id,
                                'location_dest_id': stock_move.location_dest_id.id,
                                'product_uom_id': stock_move.product_id.uom_id.id,
                                'product_id': stock_move.product_id.id,
                                'picking_id': new_picking_id
                            }
                            for lot_serial_id in claim_line.serial_lot_ids:
                                if stock_move.product_id.tracking == 'lot':
                                    move_line_vals.update({'lot_id': lot_serial_id.id,
                                                           'qty_done': stock_move.product_qty})
                                else:
                                    move_line_vals.update({'lot_id': lot_serial_id.id,
                                                           'qty_done': 1})
                                stock_move_line_obj.create(move_line_vals)
                            if not claim_line.serial_lot_ids:
                                move_line_vals.update({'qty_done': stock_move.product_qty})
                                stock_move_line_obj.create(move_line_vals)
                # end line
            if self.location_id:
                stock_picking_id = stock_picking_obj.browse(new_picking_id)
                internal_picking_id = stock_picking_obj.search(
                    [('group_id', '=', stock_picking_id.group_id.id),
                     ('location_id', '=', self.location_id.id),
                     ('picking_type_id.code', '=', 'internal'),
                     ('state', 'not in', ['cancel', 'draft'])])
                if claim_lines:
                    self.write({'internal_picking_ids': [(4, internal_picking_id.id)]})
                else:
                    self.internal_picking_id = internal_picking_id
                self.is_return_internal_transfer = True
                internal_picking_id.write({'claim_id': self.id})
            return True


