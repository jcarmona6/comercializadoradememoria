{
    "name": "RMA for Roy",
    "version": "15.0.1.0.0",
    "category": "Product",
    "author": ""
    "",
    "license": "AGPL-3",
    "depends": ["rma_ept"],
    "data": [
        # security
        "security/ir.model.access.csv",
        
        # views
        "views/rma_view.xml",
        "views/stock_picking.xml"],
    "installable": True,
}
