# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    second_validation = fields.Boolean(string="POS Stock Double Validation")
    validation_type = fields.Selection(selection=[('on_payment', 'Payment'), ('on_validation', 'Order Validation')], string="Apply Check On")