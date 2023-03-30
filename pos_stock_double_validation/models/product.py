# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def get_latest_qty(self, kwargs):
        result = {}
        config_id = self.env['pos.config'].browse(kwargs['config_id'])
        update_stock_quantities = config_id.company_id.point_of_sale_update_stock_quantities
        if update_stock_quantities and update_stock_quantities == 'closing':
            # sessions = self.env['pos.session'].search([('state', '!=', 'closed'), ('config_id', '!=', config_id.id)])
            sessions = self.env['pos.session'].search([('state', '!=', 'closed')])
            stock_result = {}
            if sessions and len(sessions):
                for session in sessions:
                    if session.order_ids and len(session.order_ids):
                        for order_id in session.order_ids:
                            for line in order_id.lines:
                                for product_id in kwargs['product_ids']:
                                    if product_id == line.product_id.id:
                                        if not stock_result.get(product_id):
                                            stock_result[product_id] = line.qty
                                        else:
                                            stock_result[product_id] = stock_result[product_id] + line.qty
            picking_type = config_id.picking_type_id
            location_id = picking_type.default_location_src_id.id
            products = self.with_context(pricelist=config_id.pricelist_id,location=location_id).browse(kwargs['product_ids'])
            for product in products:
                qty = 0
                if config_id.wk_stock_type == 'available_qty':
                    qty = product.qty_available
                elif config_id.wk_stock_type == 'forecasted_qty':
                    qty = product.virtual_available
                else:
                    qty = product.qty_available - product.outgoing_qty
                if not stock_result.get(product.id):
                    result[product.id] = qty
                else:
                    result[product.id] = qty - stock_result.get(product.id)
            return result
        else:
            picking_type = config_id.picking_type_id
            location_id = picking_type.default_location_src_id.id
            products = self.with_context(pricelist=config_id.pricelist_id,location=location_id).browse(kwargs['product_ids'])
            for product in products:
                qty = 0
                if config_id.wk_stock_type == 'available_qty':
                    qty = product.qty_available
                elif config_id.wk_stock_type == 'forecasted_qty':
                    qty = product.virtual_available
                else:
                    qty = product.qty_available - product.outgoing_qty
                result[product.id] = qty
            return result