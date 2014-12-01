import time
import pytz
from openerp import SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class purchase_order(osv.osv):

    _inherit = 'purchase.order'

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        #for po in self.browse(cr, uid, ids, context=context):
        #    if not po.expense_account_id:
        #        raise osv.except_osv(_('Expense Account Required!'),_('Please set a proper default expense account before confirm the order.'))
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)

    def _choose_account_from_po_line(self, cr, uid, po_line, context=None):
        if not po_line.expense_account_id:
            raise osv.except_osv(_('Expense Account Required!'),_('Please set a proper default expense account before confirm the order.'))
        return po_line.expense_account_id.id

    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        res = False

        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        for order in self.browse(cr, uid, ids, context=context):
            #pay_acc_id = order.partner_id.property_account_payable.id
            accs = account_obj.search(cr, uid, [('code', '=', '221000'), ('company_id', '=', order.company_id.id)], context=context)
            pay_acc_id = accs and accs[0] or order.partner_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error!'),
                    _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)

                po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)

            # get invoice data and create invoice
            inv_data = {
                'name': order.partner_ref or order.name,
                'reference': order.partner_ref or order.name,
                'account_id': pay_acc_id,
                'type': 'in_invoice',
                'partner_id': order.partner_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, inv_lines)],
                'origin': order.name,
                'fiscal_position': order.fiscal_position.id or False,
                'payment_term': order.payment_term_id.id or False,
                'company_id': order.company_id.id,
            }
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            res = inv_id
        return res

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'company_id': order_line.order_id.company_id.id,
        }


class purchase_order_line(osv.osv):
    _inherit = _name = 'purchase.order.line'

    _columns = {
        'expense_account_id': fields.many2one('account.account', 'Account', domain=[('type', 'in', ['payable', 'other'])]),
    }