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

from odoo import models, fields, api, _


class PosConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_invoice_type = fields.Selection([('single', 'Single Invoice'), ('mass', 'Multi Invoices')])

    @api.model
    def get_values(self):
        res = super(PosConfigSetting, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        pos_invoice_type = param_obj.get_param('aspl_pos_multi_invoice_ee.pos_invoice_type', default=False)
        res.update(
            pos_invoice_type=pos_invoice_type,
        )
        return res

    def set_values(self):
        res = super(PosConfigSetting, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("aspl_pos_multi_invoice_ee.pos_invoice_type",
                                                         self.pos_invoice_type)


class PosOrder(models.Model):
    _inherit = "pos.order"
    _description = "Point of Sale Orders"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
