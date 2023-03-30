# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name":  "POS Stock Double Validation",
    "summary":  """During simultaneous multiple POS sessions, the module checks whether the product added to the cart has gone out of stock on other POS or not.""",
    "category":  "Point of Sale",
    "version":  "1.0.0",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-POS-Stock-Double-Validation.html",
    "description":  """Odoo POS Stock Double Validation
POS check out of stock products
POS order validation
POS cart stock validate
POS cart inventory check
Odoo POS Stock
Show product quantity in POS
Out of stock products
Out-of-stock products POS
Added product quantities
POS product stock
Show stock pos
Manage POS stock
Product management POS""",
    "live_test_url":  "http://odoodemo.webkul.com/?module=pos_stock_double_validation&custom_url=/pos/web/#action=pos.ui",
    "depends":  ['pos_stocks'],
    "data":  [
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            "/pos_stock_double_validation/static/src/js/screens.js",
            "/pos_stock_double_validation/static/src/js/popups.js",
            "/pos_stock_double_validation/static/src/css/pos_stock_double_validation.css",
        ],
        'web.assets_qweb': [
            'pos_stock_double_validation/static/src/xml/**/*',
        ],
    },
    "images":  ['static/description/Banner.png'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  52,
    "currency":  "USD",
    "pre_init_hook":  "pre_init_check",
}
