# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_mx_edi_usage = fields.Selection(selection_add=[("00", "Por Modificar")])
