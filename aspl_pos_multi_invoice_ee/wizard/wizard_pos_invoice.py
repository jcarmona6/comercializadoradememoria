# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class WizardMassInvoice(models.TransientModel):
    _name = 'wizard.mass.invoice'

    start_date = fields.Date(string="Start Date", required=True, default=date.today())
    end_date = fields.Date(string="sEnd Date", required=True, default=date.today())
    customer_id = fields.Many2one('res.partner', string="Customers", required=True)
    pos_order_ids = fields.Many2many('pos.order', string="POS Lines")

    @api.onchange('start_date', 'end_date', 'customer_id')
    def get_pos_order(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning(_("Please enter valid date."))
        domain = [
            ('state', '=', 'paid'),
            ('partner_id', '=', self.customer_id.id),
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date)
        ]
        pos_lines_ids = self.env['pos.order'].search(domain)
        self.pos_order_ids = [(6, 0, pos_lines_ids.ids)]

    def create_invoice(self):
        lst_invoice_ids = []
        if not self.pos_order_ids:
            raise ValidationError("No order found for '{}'.".format(self.customer_id.name))
        pos_invoice_type = self.env['ir.config_parameter'].sudo().get_param(
            'aspl_pos_multi_invoice_ee.pos_invoice_type')
        if not pos_invoice_type:
            raise ValidationError("Please Configure POS Multi Invoice settings.")
        if pos_invoice_type == 'single':
            for pos_order_id in self.pos_order_ids:
                if not pos_order_id.config_id.module_account:
                    raise Warning("please enable the invoice configuration in point of sale")
                invoice_id = pos_order_id.action_pos_order_invoice()
                lst_invoice_ids.append(invoice_id['res_id'])
        elif pos_invoice_type == 'mass':
            pos_order_line_lst = []
            pos_name_lst = []
            for pos_order_id in self.pos_order_ids:
                pos_name_lst.append(pos_order_id.name)
                for each in pos_order_id.lines:
                    account_id = each.product_id.categ_id.property_account_income_categ_id
                    if not account_id:
                        account_id = each.product_id.property_account_income_id
                    if not account_id:
                        raise Warning('please define account in product category or in product')
                    pos_order_line = {
                        'product_id': each.product_id.id,
                        'account_id': account_id.id,
                        'name': each.product_id.name,
                        'quantity': each.qty,
                        'price_unit': each.price_unit,
                        'product_uom_id': each.product_uom_id.id,
                        'tax_ids': [(6, False, each.tax_ids_after_fiscal_position.ids)],
                        'price_subtotal': each.price_subtotal_incl,
                        'discount': each.discount,
                    }
                    pos_order_line_lst.append((0, 0, pos_order_line))
            invoice_id = self.env['account.move'].create({
                'partner_id': self.customer_id.id,
                'l10n_in_gst_treatment': self.customer_id.l10n_in_gst_treatment if self.customer_id.l10n_in_gst_treatment else "regular",
                'currency_id': self.env.user.company_id.currency_id.id,
                'move_type': 'out_invoice',
                'narration': "POS Mass Invoice",
                'invoice_date': date.today(),
                'date': date.today(),
                'invoice_line_ids': pos_order_line_lst,
                'ref': ",".join(pos_name_lst),
            })
            invoice_id.action_post()
            for pos_order_id in self.pos_order_ids:
                pos_order_id.account_move = invoice_id.id
                pos_order_id.state = 'invoiced'
            lst_invoice_ids.append(invoice_id.id)
        return {
            'name': _('Account Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', lst_invoice_ids)],
        }


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def button_cancel(self):
        res = super(AccountInvoice, self).button_cancel()
        pos_orders = self.env['pos.order'].search([('account_move', '=', self.id)])
        for pos_order in pos_orders:
            pos_order.state = 'paid'
            pos_order.account_move = False
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
