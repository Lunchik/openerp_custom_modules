'''Customzied Partners'''

from openerp.osv import osv, orm, fields
from openerp import netsvc

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import datetime

from openerp import SUPERUSER_ID


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'project_id': fields.many2one('account.analytic.account'),
        #'code': fields.char('Ref. No'),
    }

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'



    _columns = {
        'order_ids': fields.one2many('sale.order', 'project_id', 'Sale Order'),
        'tgt_pricelist_id': fields.many2one('product_tgt.pricelist', 'Pricelist'),
        'enduser_ids': fields.one2many('res.partner', 'project_id', string='End User'),
        'ref_doc': fields.binary('Contract Ref'),
    }

class res_enduser(osv.osv):
    ''' Contract End User '''

    _name = 'res.enduser'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'End User'),
        'contract_id': fields.many2one('sale.contract', 'Contract'),
    }




class sale_contract(osv.osv):
    _name = 'sale.contract'

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        return company_id

    def _get_current_date(self, cr, uid, context=None):
        return datetime.datetime.utcnow()


    _columns = {
        'name': fields.char('Name', required=True),
        'code': fields.char('Ref. No'),
        'amount': fields.float('Contract Value', help='Signed Amount (USD)'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'manager_id': fields.many2one('res.users', 'Account Manager'),
        'company_id': fields.many2one('res.company', 'TGT Entity'),
        'start_date': fields.date('Start Date'),
        'end_date': fields.date('End Date'),
        'order_ids': fields.one2many('sale.order', 'contract_id', 'Sale Order'),
        'tgt_pricelist_id': fields.many2one('product_tgt.pricelist', 'Pricelist'),
        'enduser_ids': fields.one2many('res.enduser', 'contract_id', string='End User'),
        'ref_doc': fields.binary('Contract Ref'),
        'description': fields.text(''),
    }

    def copy_data(self, cr, uid, ids, context=None):
        oobj = self.pool.get('account.analytic.account')
        ids = oobj.search(cr, uid, [], context=context)
        for con in oobj.browse(cr, uid, ids, context=context):
            dta = {
                'name': con.name,
                'company_id': con.company_id.id,
                'partner_id': con.partner_id.id,
                'manager_id': con.manager_id.id,
                'code': con.code,
                'start_date': con.date_start,
                'end_date': con.date,
                'description': con.description,
                'ref_doc': con.ref_doc,
            }
            self.create(cr, uid, dta, context=context)

class base_tgt_contract(osv.osv):
    _inherit = 'product_tgt.pricelist'
    _columns = {
        "contract_id": fields.many2one('sale.contract', 'Contract'),
    }


class base_tgt_contract(osv.osv):
    _inherit = "crm.lead"
    _description = "Associated Contract"
    _columns = {
        'field_name': fields.char('Field Name', size=200),
        'well_name': fields.char('Well Name', size=200),
        'tempreture_uom': fields.selection([('c', 'Celcius'), ('f', 'Farenheit')],'Temp UoM'),
        'well_deviation': fields.selection([
            ('vertical', 'Vertical'),
            ('horizontal', 'Horizontal'),
            ], 'Well Deviation', size=200),
        'depth': fields.integer('Depth'),
        'depth_unit': fields.selection([('ft', 'Feet'), ('m', 'Meter')], 'Depth Measure'),
        'conveyance': fields.selection([
                ('eline', 'E-Line'),
                ('slickline', 'Slickline'),
                ('coil_tubing', 'Coil tubing'),
                ('tractor', 'Tractor'),
                ('other', 'Other'),
            ],
            'Conveyance'),
        'land': fields.selection([('land', 'Land'), ('offshore', 'Offshore'),], 'Land / Offshore'),
        'temprature': fields.float('Temperature'),
    }

    _defaults = {
        'depth': 1000,
        'depth_unit': 'ft',
    }

    def on_change_user(self, cr, uid, id, ids, context=None):
        return {}




class sale_order(osv.osv):
    '''add company_id into sale.order
        and make shop_id hidden,
        when company_id changed
        fire on_change_company event
    '''
    _inherit = 'sale.order'

    def _sum_conveyance(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            #if sale.conveyance_ctype == 'f':
            #    res[sale.id] = 0.0 #sale.conveyance_amount
            #    continue
            res[sale.id] = sale.amount_untaxed * 0.0 #sale.conveyance_amount
            continue
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all1(self, cr, uid, ids, field_name, arg, context=None):
        # Ende
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'conveyance_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']

        for order in self.browse(cr, uid, ids, context=context):
            #if order.conveyance_ctype == 'f':
                #res[order.id]['amount_total'] += order.conveyance_amount
            res[order.id]['conveyance_total'] = 0.0 #order.conveyance_amount
            #continue
            res[order.id]['conveyance_total'] = 0.0 #res[order.id]['amount_untaxed'] * order.conveyance_amount
            res[order.id]['amount_total'] += 0.0
        return res


    def _get_default_currency(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return company_id

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        return company_id

    def _get_default_income_account(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        acc_obj = self.pool.get('account.account')
        srev = acc_obj.search(cr,uid,[('code','=','410000'),('company_id','=',company_id)])
        return srev and srev[0] or False
        



    _columns = {
        'employee_ids': fields.many2many('hr.employee', 'sale_employee_rel', 'sale_id', 'employee_id', 'Logging Engineers'),
        'asset_ids': fields.many2many('account.asset.asset','sale_asset_rel', 'sale_id', 'employee_id', 'Logging Engineers'),
        'income_account_id': fields.many2one('account.account', 'Default Income Account'),
        'contract_id': fields.many2one('sale.contract', 'Contract'),
        'project_id': fields.many2one('account.analytic.account', 'Cost Centre / Analytic', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="The analytic account related to a sales order."),
        'tax_id': fields.many2one('account.tax', 'Tax'),
        'temprature_uom': fields.selection([('c', 'Celcius'), ('f', 'Farenheit')], 'Temprature UoM'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'enduser_id': fields.many2one('res.partner', 'End User'),
        'company_id': fields.many2one('res.company', 'TGT Entity'),
        'charge_type': fields.selection([('f', 'Flat Charge'),('s', 'Survey Charge')], 'Type'),
        'field_name': fields.char('Field Name', size=200),
        'well_name': fields.char('Well Name', size=200),
        'tgt_pricelist_id': fields.many2one('product_tgt.pricelist', 'Pricelist'),
        'well_deviation': fields.selection([
            ('vertical', 'Vertical'),
            ('horizontal', 'Horizontal'),
            ], 'Well Deviation', size=200),
        'depth': fields.integer('Depth'),
        'depth_unit': fields.selection([('ft', 'Feet'), ('m', 'Meter')], 'Depth Measure'),
        'conveyance': fields.selection([
                ('eline', 'E-Line'),
                ('slickline', 'Slickline'),
                ('coil_tubing', 'Coil tubing'),
                ('tractor', 'Tractor'),
                ('other', 'Other'),
            ],
            'Conveyance'),
        'land': fields.selection([('land', 'Land'), ('offshore', 'Offshore'),], 'Land / Offshore'),
        'temprature': fields.float('Temperature'),
        'conveyance_total': fields.function(_sum_conveyance, string='Conveyance Total', type='float'),
        'amount_untaxed': fields.function(_amount_all1, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all1, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all1, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
    }

    _defaults = {
        'currency_id': _get_default_currency,
        'company_id': _get_default_company,
    }

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """

        result = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        company_id = order.income_account_id.company_id.id
        accs = self.pool.get('account.account').search(cr, uid, [('code','=','121000'), ('company_id', '=', company_id)])
        account = accs and accs[0] or False
        result.update({'account_id': account or order.income_account_id.id})
        return result


    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        return super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, context=context)
        v = {}
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
            if shop.pricelist_id.id:
                currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id
                if shop.pricelist_id.currency_id != currency_id.id:
                    self.pool.get('product.pricelist').write(cr, SUPERUSER_ID, [shop.pricelist_id.id], {'currency_id': currency_id.id}, context=context)
                v['pricelist_id'] = shop.pricelist_id.id
        elif project_id:
            company_id = self.pool.get('account.analytic.account').browse(cr, uid, project_id, context=context).company_id
            shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', company_id.id)], context=context)
            if shop_ids:
                v['shop_id'] = shop_ids[0]

        # raise ValueError, (shop_id, v)
        return {'value': v}

    def onchange_tgt_plist_id(self, cr, uid, ids, tgt_plist, context=None):
        v = {}
        #if tgt_plist:
        #    plist = self.pool.get('product_tgt.pricelist').browse(cr, uid, tgt_plist, context=context)
        #    v['conveyance_amount'] = plist.conveyance
        #    v['conveyance_ctype'] = plist.conveyance_ctype
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = {}
        domain['tgt_pricelist_id'] = [('active','=',True), ('default', '=', True), ('company_id', '=', company_id)]        
        return {'value': v, 'domain': domain}


    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        return company_id

    def _get_default_pricelist(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        pl_ids = self.pool.get('product_tgt.pricelist').search(cr, uid, [('default', '=', True), ('active', '=', True), ('company_id', '=', company_id)], context=context)
        return pl_ids and pl_ids[0] or False

    def write(self, cr, uid, ids, vals, context=None):
        if not 'company_id' in vals and not 'project_id' in vals:
            return super(sale_order, self).write(cr, uid, ids, vals, context=context)
        if not 'company_id' in vals and not 'contract_id' in vals:
            return super(sale_order, self).write(cr, uid, ids, vals, context=context)
        if not 'company_id' in vals and not 'income_account_id' in vals:
            return super(sale_order, self).write(cr, uid, ids, vals, context=context)
        contract_id = vals.get('contract_id', False)
        project_id = vals.get('project_id', False)
        income_account_id = vals.get('income_account_id', False)
        company_id = self.pool.get('sale.contract').browse(cr, uid, contract_id, context=context).company_id.id
        vals['company_id'] =  company_id
        acc_obj = self.pool.get('account.account')
        counterpart = acc_obj.search(cr, uid, [('code', '=', '410000'), ('company_id', '=', company_id)], context=context, limit=1)
        vals['income_account_id'] = counterpart and counterpart[0] or False
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        #raise ValueError, vals
        if not 'company_id' in vals and not 'project_id' in vals:
            return super(sale_order, self).create(cr, uid, vals, context=context)
        if not 'company_id' in vals and not 'contract_id' in vals:
            return super(sale_order, self).create(cr, uid, vals, context=context)
        #if not 'company_id' in vals and not 'income_account_id' in vals:
        #    return super(sale_order, self).create(cr, uid, vals, context=context)
        project_id = vals.get('project_id', False)
        contract_id = vals.get('contract_id', False)
        income_account_id = vals.get('income_account_id', False)
        company_id = self.pool.get('sale.contract').browse(cr, uid, contract_id, context=context).company_id.id
        vals['company_id'] =  company_id
        acc_obj = self.pool.get('account.account')
        counterpart = acc_obj.search(cr, uid, [('code', '=', '410000'), ('company_id', '=', company_id)], context=context, limit=1)
        vals['income_account_id'] = counterpart and counterpart[0] or False

        return super(sale_order, self).create(cr, uid, vals, context=context)

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        v = {}
        if company_id:
            shop_id = None
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', company_id)], context=context)
            if not shop_ids:
                ptids = self.pool.get('account.payment.term').search(cr, uid, [('active', '=', True)], context=context, limit=1)
                try:
                    warehouse_id = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
                    if warehouse_id:
                        warehouse_id = warehouse_id[0]
                except:
                    warehouse_id = False
                shopv = {
                    'name': company.name,
                    'company_id': company.id,
                    'payment_default_id': ptids[0],
                }
                if warehouse_id:
                    shopv['warehouse_id'] = warehouse_id

                shop_id = self.pool.get('sale.shop').create(cr, uid, shopv, context=context)
            else:
                shop_id = shop_ids[0]
            v['shop_id'] = shop_id
            domain = {'partner_id': [('customer', '=', True), ('company_id', '=', company_id)]}
            acc_obj = self.pool.get('account.account')
            srev = acc_obj.search(cr,uid,[('code','=','410000'),('company_id','=',company_id)])
            #srev = acc_obj.search(cr,uid,[('code','=','410000'),])
            #raise ValueError, srev and srev[0] or False
            v['income_account_id'] = srev and srev[0] or False
        return {'value': v,}

    def on_change_project_id(self, cr, uid, ids, project_id, context=None):
        if not project_id:
            return {}
        contract = self.pool.get('account.analytic.account').browse(cr, uid, project_id, context=context)
        

        #domain = [id.id for id in contract.enduser_ids]

        res = {}
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', contract.company_id.id)], context=context)
        if shop_ids:
            res['shop_id'] = shop_ids[0]
        res['company_id'] = contract.company_id.id
        res['tgt_pricelist_id'] = contract.tgt_pricelist_id.id

        return {'value': res}


    def on_change_contract_id(self, cr, uid, ids, contract_id, context=None):
        if not contract_id:
            return {}
        domain = {}
        cid = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        #domain['project_id'] = [('company_id', '=', cid)]
        contract = self.pool.get('sale.contract').browse(cr, uid, contract_id, context=context)
        plist_ids = self.pool.get('product_tgt.pricelist').search(cr,uid,['|',('contract_id','=',contract_id),('default','=',True)])
        domain['tgt_pricelist_id'] = ['|',('contract_id','=',contract_id),('default','=',True)]
        partner_domains = [id.partner_id.id for id in contract.enduser_ids]

        domain['enduser_id'] = [('id', 'in', partner_domains)]

        res = {}
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', contract.company_id.id)], context=context)
        if shop_ids:
            res['shop_id'] = shop_ids[0]
        res['company_id'] = contract.company_id.id

        return {'value': res, 'domain': domain}

    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            ptids = self.pool.get('account.payment.term').search(cr, uid, [('active', '=', True)], context=context, limit=1)
            warehouse_id = False
            try:
                warehouse_id = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
                if warehouse_id:
                    warehouse_id = warehouse_id[0]
            except:
                warehouse_id = False
            shopv = {
                'name': company.name,
                'company_id': company.id,
                'payment_default_id': ptids[0],
            }
            if warehouse_id:
                shopv['warehouse_id'] = warehouse_id
            shop_id = self.pool.get('sale.shop').create(cr, uid, shopv, context=context)
            # raise ValueError, self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context).name
            return shop_id
        return shop_ids[0]

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        val = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        if not part:
            return val
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        cid = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        pids = self.pool.get('res.company')._get_partner_descendance(cr, uid, cid, [cid], context)
        cids = self.pool.get('res.company').search(cr, uid, [('partner_id','in',pids)], context=context)
        val['value']['contract_id'] = False
        domain = {'contract_id':[('partner_id', '=', part.id), ('company_id', 'in', cids)]}
        val['domain'] = domain
        return val

    _defaults = {
        'company_id': _get_default_company,
        'tgt_pricelist_id': _get_default_pricelist,
        'shop_id': _get_default_shop,
        'income_account_id': _get_default_income_account,
        'depth_unit': 'ft',
        'charge_type': 'f',
    }


class sale_order_line(osv.osv):
    _name = _inherit = 'sale.order.line'

    _columns = {
        'dummy': fields.char('Dummy', size=1),
    }

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        if not line.invoiced:
            if not account_id:
                account_id = line.order_id.income_account_id and line.order_id.income_account_id.id or False
            if not account_id:
                raise osv.except_osv(_('Income Account not Set!'),
                            _('There is no Default Income Account for this Order, Please go to sale order and select proper Income Account.'))
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'company_id': line.order_id.company_id.id,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
            }

        return res

    def product_id_change(self, cr, uid, ids, pricelist,tgt_pricelist_id,charge_type,well_deviation,temprature, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        if name:
            flag = True
        context = context or {}
        lang = lang or context.get('lang',False)
        #raise ValueError, [(pricelist,tgt_pricelist_id,charge_type,well_deviation,temprature, product, qty,
        #    uom, qty_uos, uos, name, partner_id,
        #    lang, update_tax, date_order, packaging, fiscal_position, flag,  context), partner_id]
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('Before choosing a product,\n select a customer in the sales form.'))
        elif not charge_type:
            #raise osv.except_osv(_('Charge Type is not Set !'), _('Before choosing a charge,\n select a Charge Type in Contract Info tab.'))
            pass
        elif not  well_deviation:
            #raise osv.except_osv(_('Well deviation is not Defined !'), _('Before choosing a charge,\n select a well deviation in Contract Info tab.'))
            pass

        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id, context=context).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        plist = self.pool.get('product_tgt.pricelist').browse(cr, uid, tgt_pricelist_id, context=context)
        ct = {'f':'flat','s':'survey'}
        vr = {'vertical':'v','horizontal':'h'}
        product_obj = self.pool.get('product.product')
        cline_obj = self.pool.get('product_tgt.pricelist.charge.line')
        rule_obj = self.pool.get('product_tgt.pricelist.rule')
        rule_ids = []
        if well_deviation:
            rule_ids = rule_obj.search(cr, uid, [('pricelist_id', '=', plist.id),('charge_type','ilike',ct[charge_type]),('version','=',vr[well_deviation])],context=context)
        charge_ids = cline_obj.search(cr, uid, [('pricelist_rule_id', 'in', rule_ids)], context=context)
        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        fpos = fiscal_position and self.pool.get('account.tax').browse(cr, uid, fiscal_position) or False
        #raise ValueError, fpos
        if update_tax: #The quantity only have changed
            result['tax_id'] = fpos and [fpos.id] or []
        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
            result.update({'price_unit': 1.0})
        #get unit price
        if not tgt_pricelist_id:
            #warn_msg = _('You have to select a pricelist !\n'
            #        'Please set one before choosing a cahrge.')
            #warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
            result.update({'price_unit': 1.0})
        elif not well_deviation:
            result.update({'price_unit': 1.0})
        #    warn_msg = _('You have to set a well deviation !\n'
        #            'Please set Well Deviation before choosing a charge.')
        #    warning_msgs += _("No Well Deviation setting ! : ") + warn_msg +"\n\n"
        else:
            price = False
            uuom = False
            for charge in cline_obj.browse(cr, uid, charge_ids, context=context):
                if charge.product_id.id == product_obj.id:
                    price = charge.price_unit
                    uuom = charge.product_uom
                    if product_obj.uom_id.category_id.id != uuom.category_id.id:
                        uuom = False

            if not price:
                #warn_msg = _("Cannot find a pricelist line matching this Charge.\n"
                #                "You have to change either the charge or the pricelist.")

                #warning_msgs += _("No valid pricelist found ! :") + warn_msg +"\n\n"
                result.update({'price_unit': 1.0})
            else:
                result.update({'price_unit': price})
                if uuom:
                    result.update({'product_uom': uuom.id})
        if warning_msgs:
            warning = {
               'title': _('Configuration Error!'),
               'message' : warning_msgs
            }

        return {'value': result, 'domain': domain, 'warning': warning}

    def product_uom_change(self, cursor, user, ids, pricelist, tgt_pricelist_id,charge_type,well_deviation,temprature, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,context=None):
        #raise ValueError, [(pricelist,tgt_pricelist_id,charge_type,well_deviation,temprature, product, qty,
        #    uom, qty_uos, uos, name, partner_id,
        #   lang, update_tax, date_order, packaging, context), partner_id]
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.product_id_change(cursor, user, ids, pricelist, tgt_pricelist_id,charge_type,well_deviation,temprature, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, flag=True, context=context)


# Wizards, wizards, ..... wizards
class crm_make_sale(osv.osv_memory):
    """ Make sale  order for crm """

    _inherit = "crm.make.sale"

    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            ptids = self.pool.get('account.payment.term').search(cr, uid, [('active', '=', True)], context=context, limit=1)
            warehouse_id = False
            try:
                warehouse_id = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
                if warehouse_id:
                    warehouse_id = warehouse_id[0]
            except:
                warehouse_id = False
            shopv = {
                'name': company.name,
                'company_id': company.id,
                'payment_default_id': ptids[0],
            }
            if warehouse_id:
                shopv['warehouse_id'] = warehouse_id
            shop_id = self.pool.get('sale.shop').create(cr, uid, shopv, context=context)
            # raise ValueError, self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context).name
            return shop_id
        return shop_ids[0]

    _columns = {
        'shop_id': fields.many2one('sale.shop', 'TGT Entity', required=True),
    }

    _defaults = {
        'shop_id': _get_default_shop,
    }