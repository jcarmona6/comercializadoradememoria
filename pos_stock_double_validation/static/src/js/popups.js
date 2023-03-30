/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_stock_double_validation.popups', function (require) {
    "use strict";
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class SecondValidationPopup extends AbstractAwaitablePopup {}
    SecondValidationPopup.template = 'SecondValidationPopup';
    SecondValidationPopup.defaultProps = {
        title: 'Confirm ?',
        body: '',
    };

    Registries.Component.add(SecondValidationPopup);
    return SecondValidationPopup;
});