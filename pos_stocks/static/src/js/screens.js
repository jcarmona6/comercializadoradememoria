/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define("pos_stock.ProductScreen", function (require) {
  "use strict";
  const ProductScreen = require("point_of_sale.ProductScreen");
  const ProductsWidget = require("point_of_sale.ProductsWidget");
  const Registries = require("point_of_sale.Registries");

  const PosProductScreen = (ProductScreen) =>
    class extends ProductScreen {
      mounted() {
        super.mounted();
        this.env.pos.set_stock_qtys(this.env.pos.get("wk_product_qtys"));
        this.env.pos.wk_change_qty_css();
      }
    };
  Registries.Component.extend(ProductScreen, PosProductScreen);

  const PosProductsWidget = (ProductsWidget) =>
    class extends ProductsWidget {
      get productsToDisplay() {
        var self = this;
        var products = super.productsToDisplay

        // UPDATED THE PRODUCTS LIST ACCORDING TO BACKEND STOCKS CONFIGURATION
        // ===================================================================
        var product_data = self.env.pos.db.wk_product_qtys;
        if (self.env.pos.config.wk_display_stock && self.env.pos.config.wk_hide_out_of_stock) {
          var available_product = [];
          var product_data = self.env.pos.db.wk_product_qtys;
          var data_list = Object.keys(product_data);
          _.each(products, function (product) {
            if (data_list.indexOf(product.id.toString()) != -1) {
              if (product.type == "service") {
                delete self.env.pos.db.wk_product_qtys[product.id];
              }

              // Updated the quantity in the product
              // -----------------------------------
              var product_quant = self.env.pos.db.wk_product_qtys[product.id]
              if(self.env.pos.config.wk_stock_type == 'available_qty'){
                product.qty_available=product_quant
              } else if (self.env.pos.config.wk_stock_type == 'forecasted_qty'){
                product.virtual_available=product_quant
              } else {
                product.qty_available=product_quant
              }
              // -----------------------------------

              switch (self.env.pos.config.wk_stock_type) {
                case "forecasted_qty":
                  if (product.virtual_available > 0 || product.type == "service")
                  available_product.push(product);
                  break;
                  case "virtual_qty":
                    if (
                    product.qty_available - product.outgoing_qty > 0 ||
                    product.type == "service"
                    )
                    available_product.push(product);
                    break;
                    default:
                      if (product.qty_available > 0 || product.type == "service") {
                    available_product.push(product);
                  }
                }
              }
          });
          products = available_product;
        }
        // ===================================================================
        
        return products
      }
    };
  Registries.Component.extend(ProductsWidget, PosProductsWidget);
});
