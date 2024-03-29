from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    claim_id = fields.Many2one('crm.claim.ept', string='Claim')
    invoice_date = fields.Date(
        string='Invoice/Bill Date',
        readonly=True,
        index=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )

    @api.model
    def _prepare_refund(self, *args, **kwargs):
        """
        This method used to set a claim id on a create refund invoice.
        Added help by Haresh Mori @Emipro Technologies Pvt. Ltd on date 3/2/2020.
        """
        result = super(AccountMove, self)._prepare_refund(*args, **kwargs)
        if self.env.context.get('claim_id'):
            result['claim_id'] = self.env.context['claim_id']
        return result
