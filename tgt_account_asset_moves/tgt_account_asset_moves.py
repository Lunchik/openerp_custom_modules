from osv import osv, fields

import openerp.exceptions
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp import netsvc
import time
from datetime import date, datetime, timedelta
from openerp.tools import config
from openerp.tools.translate import _


MONTHS_NAMES = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('4', 'Apr'),
    ('5', 'May'),
    ('6', 'Jun'),
    ('7', 'Jul'),
    ('8', 'Aug'),
    ('9', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
]


class tgt_location(osv.osv):
    _name='tgt.location'
    _description = "TGT company Location" 
    _columns = {

                'name': fields.char('Location Description', size=64, required=True),
                'country_id': fields.many2one('res.country', 'Country'),
                'lo_cost_center':fields.many2one('account.analytic.account','Cost Center'),
                #'note': fields.char('Note', size=64), 
                'note':fields.text('Note'),
                
               }
tgt_location()



class asset_entity_move(osv.osv):
    _name='asset.entity.move'
    _description = "Asset entity moves"
    #g_cost_center = -1
    
    _columns = {

                'name': fields.char('Move Description', size=64), # will be auto sequnce
                'default_code': fields.char('Reference', size=64, select=True, required=True),
                'date':fields.date('Move Date', required=True),
                'asset':fields.many2one('account.asset.asset','Asset', required=True),
                'location':fields.many2one('tgt.location','Location', required=True),
                'cur_location':fields.many2one('tgt.location','Current Location'),
                'company_id':fields.many2one('res.company','TGT Company'), 
                'cost_center':fields.many2one('account.analytic.account','Cost Center'),
                'cur_cost_center':fields.many2one('account.analytic.account','Current Cost Center'),
                'note':fields.text('Additional Information'),
                'state':fields.selection([('draft','Draft'),('confirm','Confirmed')],'state')

                #'int_cost_center': fields.related('location', 'lo_cost_center', type='integer', string='Cost Center'),
# do uninstall then install
             
              }
   

   # def create(self, cr, uid, vals, context={}):
   #     if not 'default_code' in vals:
   #         vals['default_code'] = self.pool.get('ir.sequence').get(cr, uid, 'asset.entity.move')
   #     return super(asset_entity_move, self).create(cr, uid, vals, context)


    #def on_change_location(self, cr, uid, id, location):
    #    if location:
    #        #cost_center = self.pool.get('tgt.location').read(cr, uid, [int_cost_center], ['cost_center'])
    #        cost_center = int_cost_center   #self.pool.get('tgt.location').read(cr, uid, [int_cost_center], ['cost_center'])
    #    return {'value': {'cost_center': cost_center}}
    def on_change_asset(self, cr, uid, ids, asset, context=None):
        if asset:
            bro=self.pool.get('account.asset.asset').browse(cr,uid,asset,context=context)
            cur_location=bro.location.id
            cur_cost_center=bro.location.lo_cost_center.id
            #raise ValueError, repr(cur_cost_center)

            return {'value':{'cur_cost_center': cur_cost_center,'cur_location':cur_location}}
        return True

    def on_change_location(self, cr, uid, ids, location, context=None):
        dictionary_of_cost_centers = []
        cost_center_from_dec = 0
        if location:
            dictionary_of_cost_centers = self.pool.get('tgt.location').read(cr, uid, [location], ['lo_cost_center'])
            for dictionary_of_cost_center in dictionary_of_cost_centers:
                cost_center_from_dec = dictionary_of_cost_center['lo_cost_center']
                vals = {'cost_center':cost_center_from_dec }
            return {'value': vals}


    #def on_change_location(self, cr, uid, ids, location, context=None):
    #    global g_cost_center        
    #    if location:
    #        res['value']['cost_center']  =  self.pool.get('tgt.location').read(cr, uid, [location], ['lo_cost_center'])
 
    #def on_change_location(self, cr, uid, id, location):
    #    if location:
    #        #cost_center = self.pool.get('tgt.location').read(cr, uid, [int_cost_center], ['cost_center'])
    #        cost_center = self.pool.get('tgt.location').read(cr, uid, [int_cost_center], ['lo_cost_center'])
    #    return {'value': {'cost_center': cost_center}}


    _defaults = {
        'default_code': '/',
        'state':'draft'
        }

    def copy(self, cr, uid, id, default={}, context=None):
        dic_asset_entity_move = self.read(cr, uid, id, ['default_code'], context=context)
        if  dic_asset_entity_move['default_code']:
            default.update({
                'default_code': dic_asset_entity_move['default_code']+ _('-copy'),
            })
        return super(asset_entity_move, self).copy(cr, uid, id, default, context)
    def old_company_movement(self,cr, uid, document_id, old_category_id, asset_id,context=None):
            period_pool = self.pool.get('account.period')
            account_pool = self.pool.get('account.account')
            move_pool = self.pool.get('account.move')
            period_pool = self.pool.get('account.period')
            acc_pool = self.pool.get('account.account')
            period_id = False
            ctx = dict(context or {}, account_period_prefer_normal=True, company_id=old_category_id.company_id.id)
            #raise ValueError, (old_category_id.company_id.name, asset_id.category_id.company_id.name)
            search_periods = period_pool.find(cr, uid, document_id.date, context=ctx)
            period_id = search_periods[0]
            timenow = time.strftime('%Y-%m-%d')
            move = {
                'narration': document_id.name,
                'date': timenow,
                'ref': document_id.name,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'company_id': old_category_id.company_id.id,
            }
            line_ids = []
            debit_account_id = old_category_id.account_depreciation_id.id
            inter_company_recv_id_code = asset_id.category_id.company_id.ic_receivable_id.code
            icid = account_pool.search(cr, uid, [('company_id','=',old_category_id.company_id.id),('code','=',inter_company_recv_id_code)])
            inter_company_recv_id = icid and icid[0] or False
            #gbv_account_id = account_pool.search(cr, uid, [('code', '=', '171000'),('company_id', '=',old_category_id.company_id.id)], context=context)
            gbv_account_id = old_category_id.account_asset_id.id
            #gbv_account_id = gbv_account_id and gbv_account_id[0] or False
            debit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'account_id': debit_account_id,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'debit': asset_id.purchase_value - (asset_id.salvage_value + asset_id.value_residual),
                'credit': 0.0,
                'analytic_account_id': old_category_id.account_analytic_id and old_category_id.account_analytic_id.id or False,
                'tax_code_id': False,
                'tax_amount': 0.0,
            })
            line_ids.append(debit_line)
            debit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'account_id': inter_company_recv_id,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'debit': asset_id.value_residual,
                'credit': 0.0,
                'analytic_account_id': old_category_id.account_analytic_id and old_category_id.account_analytic_id.id or False,
                'tax_code_id': False,
                'tax_amount': 0.0,
            })
            line_ids.append(debit_line)
            credit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'partner_id': False,
                'account_id': gbv_account_id,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'debit': 0.0,
                'credit': asset_id.purchase_value,
                'analytic_account_id':  old_category_id.account_analytic_id and old_category_id.account_analytic_id.id or False,
                'tax_code_id':  False,
                'tax_amount':  0.0,
            })
            line_ids.append(credit_line)
            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)


    def new_company_movement(self,cr, uid, document_id,  asset_id,context=None):
            period_pool = self.pool.get('account.period')
            account_pool = self.pool.get('account.account')
            move_pool = self.pool.get('account.move')
            period_pool = self.pool.get('account.period')
            acc_pool = self.pool.get('account.account')
            period_id = False
            ctx = dict(context or {}, account_period_prefer_normal=True, company_id=asset_id.category_id.company_id.id)
            search_periods = period_pool.find(cr, uid, document_id.date, context=ctx)
            period_id = search_periods[0]
            ppp = period_pool.browse(cr, uid, period_id, context=context)
            #raise ValueError, (asset_id.category_id.company_id.name, ppp.company_id.name)
            timenow = time.strftime('%Y-%m-%d')
            move = {
                'narration': document_id.name,
                'date': timenow,
                'ref': document_id.name,
                'journal_id': asset_id.category_id.journal_id.id,
                'period_id': period_id,
                'company_id': asset_id.category_id.company_id.id,
            }
            line_ids = []
            credit_account_id = asset_id.category_id.account_depreciation_id.id
            inter_company_payable_id = asset_id.category_id.company_id.ic_payable_id.id

            #gbv_account_id = account_pool.search(cr, uid, [('code', '=', '171000'),('company_id', '=',asset_id.category_id.company_id.id)], context=context)
            gbv_account_id = asset_id.category_id.account_asset_id.id
            credit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'account_id': credit_account_id,
                'journal_id': asset_id.category_id.journal_id.id,
                'period_id': period_id,
                'debit': 0.0,
                'credit': asset_id.purchase_value - (asset_id.salvage_value + asset_id.value_residual),
                'analytic_account_id': asset_id.category_id.account_analytic_id and asset_id.category_id.account_analytic_id.id or False,
                'tax_code_id': False,
                'tax_amount': 0.0,
            })
            line_ids.append(credit_line)
            credit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'account_id': inter_company_payable_id,
                'journal_id': asset_id.category_id.journal_id.id,
                'period_id': period_id,
                'debit': 0.0,
                'credit': asset_id.value_residual,
                'analytic_account_id': asset_id.category_id.account_analytic_id and asset_id.category_id.account_analytic_id.id or False,
                'tax_code_id': False,
                'tax_amount': 0.0,
            })
            line_ids.append(credit_line)
            debit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'partner_id': False,
                'account_id': gbv_account_id,
                'journal_id': asset_id.category_id.journal_id.id,
                'period_id': period_id,
                'debit': asset_id.purchase_value,
                'credit': 0.0,
                'analytic_account_id':  asset_id.category_id.account_analytic_id and asset_id.category_id.account_analytic_id.id or False,
                'tax_code_id':  False,
                'tax_amount':  0.0,
            })
            line_ids.append(debit_line)
            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
    
    def confirm(self,cr,uid,ids,context=None):
        
            bro=self.browse(cr, uid, ids[0], context=context)
            if bro.company_id.id:
                
                if bro.company_id.id == bro.asset.company_id.id:

                    raise osv.except_osv(_('Error!'),_("You can't move the asset to the same company"))
                elif bro.location.id== bro.cur_location.id:
                    raise osv.except_osv(_('Error!'),_("You can't move the asset to the same location"))
                else:
                    
                    new_com=bro.company_id.id
                    new_cat=bro.company_id.asset_category.id
                    new_loc=bro.location.id
                    old_category_id = bro.asset.category_id
                    self.pool.get('account.asset.asset').write(cr,uid,bro.asset.id,{'company_id':new_com,'category_id':new_cat,'location':new_loc},context=context)
                    bro=self.browse(cr, uid, ids[0], context=context)
                    self.old_company_movement(cr, uid, bro, old_category_id, bro.asset,context=None)
                    self.new_company_movement(cr,uid,bro,bro.asset,context=context)
                    self.write(cr,uid,ids, {'state':'confirm'}, context=context)
            else:
            
                if bro.location.id== bro.cur_location.id:
                    raise osv.except_osv(_('Error!'),_("You can't move the asset to the same location"))
                else:

                    new_loc=bro.location.id
                    self.pool.get('account.asset.asset').write(cr,uid,bro.asset.id,{'location':new_loc},context=context)
                    self.write(cr,uid,ids, {'state':'confirm'}, context=context)


            return True


    def create(self, cr, uid, vals, context=None):

        #global g_cost_center
        
        if context is None:
            context = {}
        if not 'default_code' in vals or vals['default_code'] == '/':
            vals['default_code'] = self.pool.get('ir.sequence').get(cr, uid, 'asset.entity.move')
            #vals['cost_center'] = g_cost_center # fields.related('location', 'lo_cost_center', type='integer') #int_cost_center #self.pool.get('tgt.location').read(cr, uid, [int_cost_center], ['cost_center']
        
        return super(asset_entity_move, self).create(cr, uid, vals, context)
    

    
            
asset_entity_move()



class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'


    _columns = {
        #'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic account'),
        'location': fields.many2one('tgt.location', 'Asset Current Location'),
        'child_category': fields.many2one('account.asset.category', 'Asset Category'),
        'method_period': fields.integer('Period Length', help="State here the time between 2 depreciations, in months", required=True),
        
    }
    _defaults = {
        'method_period': 1,
    }

    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        code = ''
        for rs in result:
            if rs.code:
                code = rs.code
            name = "%s (%s)" % (rs.name, code)
            res += [(rs.id, name)]
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('code', 'ilike', name)]+ args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', 'ilike', name)]+ args, limit=limit, context=context)#fix it ilike should be replace with operator

        return self.name_get(cr, user, ids, context=context)

    def create(self, cr, uid, vals, context=None):
        vals['method_period'] = 1
        return super(account_asset_asset, self).create(cr, uid, vals, context=context)

    def create_clearing_entries(self,cr, uid,ids,context=None):
            move_pool= self.pool.get('account.move')
            document_id=self.browse(cr, uid, ids[0], context=context)
            old_category_id= document_id.child_category
            if not old_category_id:
                old_category_id = document_id.category_id
            asset_id=document_id
            period_pool = self.pool.get('account.period')
            account_pool = self.pool.get('account.account')
            period_id = False
            ctx = dict(context or {}, account_period_prefer_normal=True, company_id=old_category_id.company_id.id)
            timenow = time.strftime('%Y-%m-%d')
            search_periods = period_pool.find(cr, uid, timenow, context=ctx)
            period_id = search_periods[0]
            timenow = time.strftime('%Y-%m-%d')
            move = {
                'narration': document_id.name,
                'date': timenow,
                'ref': document_id.name,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'company_id': old_category_id.company_id.id,
            }
            line_ids = []
            debit_account_id = old_category_id.account_asset_id.id
            #inter_company_recv_id = account_pool.search(cr, uid, [('code', '=', '123000'),('company_id', '=',old_category_id.company_id.id)], context=context)
            #inter_company_recv_id = inter_company_recv_id and inter_company_recv_id[0] or False

            gbv_account_id = old_category_id.account_asset_new_cr.id
            #gbv_account_id = gbv_account_id and gbv_account_id[0] or False
            debit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'account_id': debit_account_id,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'debit': asset_id.purchase_value,
                'credit': 0.0,
                'analytic_account_id': old_category_id.account_analytic_id and old_category_id.account_analytic_id.id or False,
                'tax_code_id': False,
                'tax_amount': 0.0,
            })
            line_ids.append(debit_line)
           
            credit_line = (0, 0, {
                'name': document_id.name,
                'date': timenow,
                'partner_id': False,
                'account_id': gbv_account_id,
                'journal_id': old_category_id.journal_id.id,
                'period_id': period_id,
                'debit': 0.0,
                'credit': asset_id.purchase_value,
                'analytic_account_id':  old_category_id.account_analytic_id and old_category_id.account_analytic_id.id or False,
                'tax_code_id':  False,
                'tax_amount':  0.0,
            })
            line_ids.append(credit_line)
            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)

    def validate(self, cr, uid, ids, context=None):
        self.create_clearing_entries(cr,uid,ids,context=None)

        if context is None:
            context = {}

        return self.write(cr, uid, ids, {
            'state':'open'
        }, context)

    def create_move(self, cr, uid, ids, context=None):
        can_close = False
        if context is None:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = context.get('depreciation_date') or time.strftime('%Y-%m-%d')
            ctx = dict(context, account_period_prefer_normal=True, company_id=line.asset_id.company_id.id)
            period_ids = period_obj.find(cr, uid, depreciation_date, context=ctx)
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = (line.asset_id.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = line.asset_id.name
            reference = line.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
            analytic_account_id = line.asset_id.category_id.account_analytic_id.id
            if line.asset_id.location:
                if line.asset_id.location.lo_cost_center:
                    analytic_account_id = line.asset_id.location.lo_cost_center.id
            raise ValueError, analytic_account_id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                'analytic_account_id': analytic_account_id,
                'date': depreciation_date,
                'asset_id': line.asset_id.id
            })
            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids


    def compute_depreciation_board(self, cr, uid, ids, context=None):
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        currency_obj = self.pool.get('res.currency')
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)],order='depreciation_date desc')
            old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)

            amount_to_depr = residual_amount = asset.value_residual
            if asset.prorata:
                depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
                depreciation_date = datetime(depreciation_date.year, depreciation_date.month, 1)
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                #if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if (len(posted_depreciation_line_ids)>0):
                    last_depreciation_date = datetime.strptime(depreciation_lin_obj.browse(cr,uid,posted_depreciation_line_ids[0],context=context).depreciation_date, '%Y-%m-%d')
                    depreciation_date = (last_depreciation_date+relativedelta(months=+asset.method_period))
                else:
                    depreciation_date = datetime(purchase_date.year, 1, 1)
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
                company_currency = asset.company_id.currency_id.id
                current_currency = asset.currency_id.id
                # compute amount into company currency
                amount = currency_obj.compute(cr, uid, current_currency, company_currency, amount, context=context)
                residual_amount -= amount
                vals = {
                     'amount': amount,
                     'asset_id': asset.id,
                     'sequence': i,
                     'name': str(asset.id) +'/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
                     'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(cr, uid, vals, context=context)
                # Considering Depr. Period as months
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
        return True

    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
        #by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                if asset.prorata:
                    amount = amount_to_depr / asset.method_number
                    days = total_days - float(depreciation_date.strftime('%j'))
                    #raise ValueError, ('c', amount, undone_dotation_number)
                    #if i == 1:
                    #    amount = (amount_to_depr / asset.method_number) / total_days * days
                    #    raise ValueError, ('c', amount, undone_dotation_number)
                    #elif i == undone_dotation_number:
                    #    amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
                    #    raise ValueError, ('a', amount)
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                if asset.prorata:
                    days = total_days - float(depreciation_date.strftime('%j'))
                    if i == 1:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * days
                    elif i == undone_dotation_number:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
        return amount

    def _compute_board_undone_dotation_nb(self, cr, uid, asset, depreciation_date, total_days, context=None):
        undone_dotation_number = asset.method_number
        if asset.method_time == 'end':
            end_date = datetime.strptime(asset.method_end, '%Y-%m-%d')
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = (datetime(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+asset.method_period))
                undone_dotation_number += 1
        #if asset.prorata:
        #    undone_dotation_number += 1
        return undone_dotation_number


class account_asset_category(osv.osv):
    _inherit = 'account.asset.category'
    _description = 'Asset category Subcategories Support'

    _columns = {
        'parent_id': fields.many2one('account.asset.category', 'Parent Category')
    }


class res_company(osv.osv):
    _inherit = 'res.company'


    _columns = {
        
        'asset_category': fields.many2one('account.asset.category', 'Asset Category'),
        'ic_receivable_id': fields.many2one('account.account', 'I/C Receivable Account'),
        'ic_payable_id': fields.many2one('account.account', 'I/C Payable Account'),
        
    }


class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    def create_move(self, cr, uid, ids, context=None):
        can_close = False
        if context is None:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = context.get('depreciation_date') or time.strftime('%Y-%m-%d')
            ctx = dict(context, account_period_prefer_normal=True, company_id=line.asset_id.company_id.id)
            period_ids = period_obj.find(cr, uid, depreciation_date, context=ctx)
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = (line.asset_id.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = line.asset_id.name
            reference = line.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
            analytic_account_id = line.asset_id.category_id.account_analytic_id.id
            if line.asset_id.location:
                if line.asset_id.location.lo_cost_center:
                    analytic_account_id = line.asset_id.location.lo_cost_center.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                'analytic_account_id': analytic_account_id,
                'date': depreciation_date,
                'asset_id': line.asset_id.id
            })
            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids
    
class tgt_asset_number(osv.osv):
    _name='tgt.asset.number'
    _description = "TGT Asset number for Utilization" 

    def _get_eq_date(self, cr, uid, ids, field_names, arg=None, context=None):
        ''' Get Equivelance date'''
        result = {}
        if not ids:
            return {}
        cr.execute('''SELECT id, month, year FROM tgt_asset_number WHERE id in %s''', (tuple(ids),))
        res = cr.fetchall()
        for r in res:
            id, month, year = tuple(r)
            result[id] = datetime(int(year), int(month), int(month))
        return result

    _columns = {

                'location_id': fields.many2one('res.country', 'Location', required=True),
                'mon': fields.function(_get_eq_date, method=True, string='Date', args=None, type='date', store=True),
                'month': fields.selection(MONTHS_NAMES, 'Month'),
                'year': fields.integer('Year'),                
                'job_cat': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Tool Category', required=True),
                'count':fields.float('Number of Assets', help="Input the number of assets of specified type in specified location", required=True),
                
               }

    _defaults = {
        'year': datetime.now().year,
        'month': str(datetime.now().month),
    }   

    _sql_constraints = [('unique_set', 'unique(location_id,mon,job_cat)', 'Error! This set (Location, Tool, Period) already exists!')]

tgt_asset_number()