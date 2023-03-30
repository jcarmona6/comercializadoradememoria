/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_stock_double_validation.screens', function (require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc')
    const { Gui } = require('point_of_sale.Gui');

    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            _onClickPay() {
                var self = this;
                var order = self.env.pos.get_order();
                var lines = order.get_orderlines();
                if(lines.length > 0 && self.env.pos.config.second_validation && self.env.pos.config.validation_type == 'on_payment')
                    self.second_validation(self.cashregister, "payment", order);
                else
                    self.showScreen('PaymentScreen');
            }
            second_validation(options, type, order){
                var self = this;
                var lines = order.get_orderlines();
                var product_ids = [];
                _.each(lines, line => {
                    product_ids.push(line.product.id);
                });
                rpc.query({
                    model: 'product.product',
                    method: 'get_latest_qty',
                    args: [{'config_id': self.env.pos.config.id,'product_ids': product_ids,}]
                })
                .catch(function(unused, event){
                    Gui.showScreen('ErrorPopup',{
                        title: 'Unable To Fetch Stock Details.',
                        body:  'Please make sure you are connected to the network.',
                    });
                })
                .then(function(product_qty_list){
                    for(let p_id in product_qty_list){
                        if(self.env.pos.attributes.wk_product_qtys[p_id] != product_qty_list[p_id]){
                            if(self.env.pos.get('wk_product_qtys')){
                                var wk_product_qtys = self.env.pos.get('wk_product_qtys')
                                wk_product_qtys[p_id] = product_qty_list[p_id];
                                self.env.pos.set_stock_qtys(wk_product_qtys);
                                self.env.pos.wk_change_qty_css();
                            }
                        }
                        self.stock_check(options, type, order);
                    }
                });
            }
            stock_check(options, type, order){
                var self = this;
                var lines = order.get_orderlines();
                var availability = [];
                if (!self.env.pos.config.wk_continous_sale && self.env.pos.config.wk_display_stock && !order.is_return_order) {
                    var added_product_ids = [];
                    _.each(lines, line => {
                        var product = line.product;
                        if(!added_product_ids.includes(product.id)){
                            added_product_ids.push(product.id);
                            var value = self.env.pos.get('wk_product_qtys')[product.id] - line.quantity
                            if(value < self.env.pos.config.wk_deny_val){
                                let backend_qty =  self.env.pos.attributes.wk_product_qtys[product.id];
                                availability.push({'name': product.display_name, 'ordered': backend_qty - value, 'available': backend_qty - self.env.pos.config.wk_deny_val});
                            }
                        }
                    });
                    if(availability.length != 0){
                        Gui.showPopup('SecondValidationPopup', {
                            'availability_list': availability,
                        });
                    }else
                        self.payment_proceed();
                }
            }
            payment_proceed(options){
                this.showScreen('PaymentScreen');
            }
    }
    Registries.Component.extend(ProductScreen, PosProductScreen);

    const PosPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        async validateOrder(isForceValidate, two_step_done=false) {
            var self = this;
            var order = self.env.pos.get_order();
            var lines = order.get_orderlines();
            if(two_step_done ==  true)
                super.validateOrder(isForceValidate);
            else if(lines.length > 0 && self.env.pos.config.second_validation && self.env.pos.config.validation_type == 'on_validation')
                self.second_validation(isForceValidate, "validation", order);
            else
                super.validateOrder(isForceValidate);
        }
        second_validation(options, type, order){
            var self = this;
            var lines = order.get_orderlines();
            var product_ids = [];
            _.each(lines, line => {
                product_ids.push(line.product.id);
            });
            rpc.query({
                model: 'product.product',
                method: 'get_latest_qty',
                args: [{'config_id': self.env.pos.config.id,'product_ids': product_ids,}]
            })
            .catch(function(unused, event){
                Gui.showScreen('ErrorPopup',{
                    title: 'Unable To Fetch Stock Details.',
                    body:  'Please make sure you are connected to the network.',
                });
            })
            .then(function(product_qty_list){
                for(let p_id in product_qty_list){
                    if(self.env.pos.attributes.wk_product_qtys[p_id] != product_qty_list[p_id]){
                        if(self.env.pos.get('wk_product_qtys')){
                            var wk_product_qtys = self.env.pos.get('wk_product_qtys')
                            wk_product_qtys[p_id] = product_qty_list[p_id];
                            self.env.pos.set_stock_qtys(wk_product_qtys);
                            self.env.pos.wk_change_qty_css();
                        }
                    }
                    self.stock_check(options, type, order);
                }
            });
        }
        stock_check(options, type, order){
            var self = this;
            var lines = order.get_orderlines();
            var availability = [];
            if (!self.env.pos.config.wk_continous_sale && self.env.pos.config.wk_display_stock && !order.is_return_order) {
                var added_product_ids = [];
                _.each(lines, line => {
                    var product = line.product;
                    if(!added_product_ids.includes(product.id)){
                        added_product_ids.push(product.id);
                        var value = self.env.pos.get('wk_product_qtys')[product.id] - line.quantity
                        if(value < self.env.pos.config.wk_deny_val){
                            let backend_qty =  self.env.pos.attributes.wk_product_qtys[product.id];
                            availability.push({'name': product.display_name, 'ordered': backend_qty - value, 'available': backend_qty - self.env.pos.config.wk_deny_val});
                        }
                    }
                });
                if(availability.length != 0){
                    Gui.showPopup('SecondValidationPopup', {
                        'availability_list': availability,
                    });
                }else
                    self.proceed_validation(options);
            }
        }
        proceed_validation(options){
            this.validateOrder(options, true)
        }
    }
    Registries.Component.extend(PaymentScreen, PosPaymentScreen);
});