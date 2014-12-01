'''Customzied Partners'''

from openerp.osv import osv, orm, fields
from openerp import netsvc


class product_product(osv.osv):
    _inherit = 'product.product'

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            return (d['id'], name)
        result = []
        for product in self.browse(cr, user, ids, context=context):
            mydict = {
                'id': product.id,
                'name': u'[%s] - %s' % (product.product_tmpl_id.categ_id.name, product.name),
                'default_code': product.default_code,
                'variants': product.variants
            }
            result.append(_name_get(mydict))
        return result

    _columns = {
        'name_template': fields.related('product_tmpl_id', 'name', string="Template Name", type='char', size=128, store=True, select=True),
        'tool_id': fields.many2one('product.product', 'Related tool'),
        'job_cat':fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category')
    }

    _defaults = {
        'description': u'Set Description For this Charge',
        'job_cat':'other',
    }

    #Pricelist override
    def price_get(self, cr, uid, ids, ptype='list_price', context=None):
        if context is None:
            context = {}
        if 'currency_id' in context:
            pricetype_obj = self.pool.get('product.price.type')
            price_type_id = pricetype_obj.search(cr, uid, [('field','=',ptype)])[0]
            price_type_currency_id = pricetype_obj.browse(cr,uid,price_type_id).currency_id.id

        res = {}
        product_uom_obj = self.pool.get('product.uom')
        product_tgt_pl_obj = self.pool.get('product_tgt.pricelist')
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = product[ptype] or 0.0
            if ptype == 'list_price':
                res[product.id] = (res[product.id] * (product.price_margin or 1.0)) + \
                        product.price_extra
            if 'uom' in context:
                uom = product.uom_id or product.uos_id
                res[product.id] = product_uom_obj._compute_price(cr, uid,
                        uom.id, res[product.id], context['uom'])
            # Convert from price_type currency to asked one
            if 'currency_id' in context:
                # Take the price_type currency from the product field
                # This is right cause a field cannot be in more than one currency
                res[product.id] = self.pool.get('res.currency').compute(cr, uid, price_type_currency_id,
                    context['currency_id'], res[product.id],context=context)
        for p in res:
            res[p] = p * 100
        return res

class product_category(osv.osv):
    _inherit = 'product.category'

    _columns = {
        'tool_ids': fields.one2many('product.product', 'tool_id', string='Related Tools'),
    }


class product_pricelist(osv.osv):
    _name = 'product_tgt.pricelist'

    _columns = {
        'name': fields.char('Name', size=150, required=True),
        'active': fields.boolean('Active', help="uncheck this to make pricelist invisible"),
        'rule_ids': fields.one2many('product_tgt.pricelist.rule', 'pricelist_id', string='Pricelist Rules'),
        'company_id': fields.many2one('res.company', 'TGT Entity'),
        'default': fields.boolean('Default Pricelist', help="default means this pricelist will appear as a default pricelist for all new saleorder"),
        "field": fields.selection([('list_price', 'list_price')], "Product Field", size=32, required=True, help="Associated field in the product form."),

        #'conveyance': fields.float('Conveyance', required=True, help="the conveyance amount, \n if conveyance charge type is percentage, an amount is less than 1"),
        #'conveyance_ctype': fields.selection([('f', 'Fixed'),('p', 'Percentage')], 'Conveyance Charge', required=True),
    }

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        return company_id.id

    _defaults = {
        #'conveyance': 0.10,
        #'conveyance_ctype': 'f',
        'active': True,
        'field': 'list_price',
        'company_id': _get_default_company,
    }

    


class pricelist_charge_line(osv.osv):
    _name = 'product_tgt.pricelist.charge.line'

    _columns = {
        'product_id': fields.many2one('product.product', 'Charge', required=True, context="{'group_by':'categ_id'}"),
        'product_uom': fields.many2one('product.uom', 'UoM', required=True),
        'price_unit': fields.float('Unit Price'),
        'pricelist_rule_id': fields.many2one('product_tgt.pricelist.rule', 'Pricelist Rule'),
    }

    def product_id_change(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {}
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        domain = {}
        value = {}
        domain['product_uom'] = [('category_id', '=', product.uom_id.category_id.id)]
        value['product_uom'] = product.uom_id.id
        return {'value': value, 'domain': domain}

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.browse(cr, uid, ids, context=context)
        res = []
        for record in reads:
            name = record.product_id.name
            res.append((record.id, name))
        return res

    _defaults = {
        'price_unit': 1.0,
    }


class pricelist_rule(osv.osv):
    _name = 'product_tgt.pricelist.rule'

    _columns = {
        'name': fields.char('Name', size=150, required=True),
        'pricelist_id': fields.many2one('product_tgt.pricelist', 'Pricelist'),
        'version': fields.selection([('h', 'Horizontal'), ('v', 'Vertical')], 'Deviation Version', required=True, help="Deviation Version as every well has only one type of deviation."),
        'charge_type': fields.selection([
            ('flat', 'Flat Charge'),
            ('survey', 'Survey Charge'),
            ], 'Charge Type', required=True, help="refere to saleorder well information as this will be matched by charge type"),
        'land_offshore': fields.selection([
            ('land', 'Land'),
            ('offshore', 'Offshore'),
            ], 'Land / Offshore', required=True, help="Well Location"),
        'charge_ids': fields.one2many('product_tgt.pricelist.charge.line', 'pricelist_rule_id', string='Charges'),
    }

    _defaults = {
        'version': 'h',
    }
