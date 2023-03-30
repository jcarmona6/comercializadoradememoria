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

{
    'name': 'POS Multi Invoice (Enterprise)',
    'summary': 'Create Muliple Invoice of POS Orders (Enterprise)',
    'category': 'Point of Sale',
    'version': '1.0.0',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'sequence': 1,
    'description': """
This module allows user to create combine/separate invoice for selected PoS orders.
    """,
    'price': 40.00,
    'currency': 'EUR',
    'depends': ['base', 'point_of_sale', 'account', 'l10n_in'],
    'images': ['static/description/main_screenshot.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_view.xml',
        'views/res_config_setting.xml',
        'wizard/wizard_pos_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
