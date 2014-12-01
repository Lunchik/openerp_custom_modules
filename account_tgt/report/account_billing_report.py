from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields


def get_sql_by(filter):
    sql = """
    
        select partner_id as id, (select name from res_partner where id=o.partner_id) as partner,
                        
                    (select name from res_country where id=(select country_id from res_partner where id=o.partner_id)) as country,
                    currency_id,
                (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 0 and (a.{filter} - a.date_invoice) <= 30 and
                 a.partner_id=o.partner_id) as "a0_30",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 31 and (a.{filter} - a.date_invoice) <= 60 and
                 a.partner_id=o.partner_id) as "a31_60",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 61 and (a.{filter} - a.date_invoice) <= 90 and
                 a.partner_id=o.partner_id) as "a61_90",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 91 and (a.{filter} - a.date_invoice) <= 120 and
                 a.partner_id=o.partner_id) as "a91_120",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 121 and (a.{filter} - a.date_invoice) <= 150 and
                 a.partner_id=o.partner_id) as "a121_150",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 151 and (a.{filter} - a.date_invoice) <= 365 and
                 a.partner_id=o.partner_id) as "a151_365",

                 (select sum(a.amount_total) from account_invoice a where 
                (a.{filter} - a.date_invoice) >= 366 and (a.{filter} - a.date_invoice) <= 547 and
                 a.partner_id=o.partner_id) as "a366_547"

                 
                from account_invoice o where type='out_invoice' and state not in ('draft', 'paid')
                group by partner_id, currency_id
    """
    return sql.format(filter=filter)


class aging_cache(osv.osv):
    _name = 'account.billing.cache'
    _description = "Account Billing Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.a0_30,
                obj.a31_60,
                obj.a61_90,
                obj.a91_120,
                obj.a121_150,
                obj.a151_365,
                obj.a366_547)
            res[obj.id] = su
        return res


    _columns = {
        'partner': fields.char('Partner'),
        'country': fields.char('Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'total': fields.function(_total, type="float", method=True, string='Total', store=False),
        'a0_30': fields.float('0-30'),
        'a31_60': fields.float('31-60'),
        'a61_90': fields.float('61-90'),
        'a91_120': fields.float('91-120'),
        'a121_150': fields.float('121-150'),
        'a151_365': fields.float('151-365'),
        'a366_547': fields.float('366-547'),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'ar_aging_cache')
        cr.execute("create or replace view ar_aging_cache as ({})".format(get_sql_by('date_invoice')))


aging_cache()



class AccountBillingReport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Account Billing Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue_gray;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def get_fiscalyears(self, fisyear):
        self.cr.execute("""
            SELECT y.id FROM account_fiscalyear y WHERE 
            date_start>=(
                SELECT date_start FROM account_fiscalyear WHERE id=%(fisid)s
            ) AND date_stop<=(
                SELECT date_stop FROM account_fiscalyear WHERE id=%(fisid)s 
            )
        """, {'fisid': fisyear})
        res = self.cr.fetchall()
        return [i[0] for i in res]



    def generate(self):

        self.sheet.write(0, 1, 'Billing Month', self.style)
        self.sheet.write(0, 2, 'Invoice date', self.style)
        self.sheet.write(0, 3, 'TGT Entity', self.style)
        self.sheet.write(0, 4, 'Customer Name', self.style)
        self.sheet.write(0, 5, 'End User', self.style)
        self.sheet.write(0, 6, 'Country', self.style)
        self.sheet.write(0, 7, 'Invoice Number', self.style)
        self.sheet.write(0, 8, 'Job details', self.style)
        self.sheet.write(0, 9, 'Currency', self.style)
        self.sheet.write(0, 10, 'Original Amount', self.style)
        #self.sheet.write(0, 11, 'Original Amount in USD', self.style)

        sobj = self.pool.get('account.invoice')
        #raise ValueError, self.data
        fisids = self.get_fiscalyears(self.data[0]['year'][0])

        ids = sobj.search(self.cr, self.uid, [('period_id.fiscalyear_id','in',fisids)], context=self.context)

        records = sobj.browse(self.cr, self.uid, ids, context=self.context)

        i = 1
        sale_obj = self.pool.get('sale.order')
        #raise ValueError, self.data
        for rec in records:
            sale = None
            so_ids = sale_obj.search(self.cr, self.uid, [('invoice_ids','in',[rec.id]),], context=self.context)
            if so_ids:
                sale = sale_obj.browse(self.cr, self.uid, so_ids[0], context=self.context)
            last_payment = ''
            if self.data[0]['filter'] == 'date_invoice':
                tt = rec.date_invoice
                if not tt:
                    tt = rec.date_due
                last_payment = tt

            else:
                tt = rec.date_due
                if not tt:
                    tt = rec.date_invoice
                last_payment = tt

            last_paymentf = last_payment and datetime.strptime(last_payment, '%Y-%m-%d').strftime('%b-%y') or '-'
            
            last_payment = last_payment and  datetime.strptime(last_payment,'%Y-%m-%d') or ''
            
            self.sheet.write(i, 1, last_paymentf)
            self.sheet.write(i, 2, last_payment and last_payment.strftime('%d %b %Y') or 'N/A')
            self.sheet.write(i, 3, rec.company_id.name)
            self.sheet.write(i, 4, rec.partner_id.name)
            #self.sheet.write(i, 5, u', '.join([n.name for n in sale.enduser_ids]))
            self.sheet.write(i, 5, sale and sale.enduser_id.name or '-')
            self.sheet.write(i, 6, rec.partner_id.country_id.name)
            self.sheet.write(i, 7, rec.number and rec.number or 'N/A')
            self.sheet.write(i, 8, '{} - {}'.format(sale and sale.well_name or '-', sale and sale.field_name or '-'))
            self.sheet.write(i, 9, rec.currency_id.name)
            self.sheet.write(i, 10, rec.amount_total)
            #calculate original amount in USD
            company_curr = rec.company_id.currency_id
            amt = rec.amount_total
            if rec.currency_id.id != company_curr.id:
                amt = self.pool.get('res.currency').compute(self.cr, self.uid, rec.currency_id.id, company_curr.id, rec.amount_total, context=self.context)
            #self.sheet.write(i, 11, amt)

            i += 1

        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp



class AccountReceivableReport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Account Receivable Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue_gray;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def get_fiscalyears(self, fisyear):
        self.cr.execute("""
            SELECT y.id FROM account_fiscalyear y WHERE 
            date_start>=(
                SELECT date_start FROM account_fiscalyear WHERE id=%(fisid)s
            ) AND date_stop<=(
                SELECT date_stop FROM account_fiscalyear WHERE id=%(fisid)s 
            )
        """, {'fisid': fisyear})
        res = self.cr.fetchall()
        return [i[0] for i in res]


    def generate(self):

        self.sheet.write(0, 1, 'Billing Month', self.style)
        self.sheet.write(0, 2, 'Invoice date', self.style)
        self.sheet.write(0, 3, 'TGT Entity', self.style)
        self.sheet.write(0, 4, 'Customer Name', self.style)
        self.sheet.write(0, 5, 'End User', self.style)
        self.sheet.write(0, 6, 'Country', self.style)
        self.sheet.write(0, 7, 'Invoice Number', self.style)
        self.sheet.write(0, 8, 'Job details', self.style)
        self.sheet.write(0, 9, 'Currency', self.style)
        self.sheet.write(0, 10, 'Original Value', self.style)
        self.sheet.write(0, 11, 'Remaining Value', self.style)
        self.sheet.write(0, 12, 'days late', self.style)

        sobj = self.pool.get('account.invoice')

        fisids = self.get_fiscalyears(self.data[0]['year'][0])

        ids = sobj.search(self.cr, self.uid, [('state','in',['draft','open'])], context=self.context)

        records = sobj.browse(self.cr, self.uid, ids, context=self.context)


        i = 1
        sale_obj = self.pool.get('sale.order')
        now = datetime.today()

        for rec in records:
            sale = None
            so_ids = sale_obj.search(self.cr, self.uid, [('invoice_ids','in',[rec.id]),], context=self.context)
            if so_ids:
                sale = sale_obj.browse(self.cr, self.uid, so_ids[0], context=self.context)
            last_payment = ''
            if self.data[0]['filter'] == 'date_invoice':
                last_payment = datetime.strptime(rec.date_invoice, '%Y-%m-%d')
            else:
                tt = rec.date_due
                if not tt:
                    tt = rec.date_invoice
                last_payment = datetime.strptime(tt, '%Y-%m-%d')
            
            self.sheet.write(i, 1, last_payment.strftime('%b-%y'))
            self.sheet.write(i, 2, last_payment.strftime('%d %b %Y'))
            self.sheet.write(i, 3, rec.company_id.name)
            self.sheet.write(i, 4, rec.partner_id.name)
            #self.sheet.write(i, 5, u', '.join([n.name for n in sale.enduser_ids]))
            self.sheet.write(i, 5, sale and sale.enduser_id.name)
            self.sheet.write(i, 6, rec.partner_id.country_id.name)
            self.sheet.write(i, 7, rec.number and rec.number or 'N/A')
            self.sheet.write(i, 8, '{} - {}'.format(sale and sale.well_name, sale and sale.field_name))
            self.sheet.write(i, 9, rec.currency_id.name)
            self.sheet.write(i, 10, rec.amount_total)
            #calculate original amount in USD
            company_curr = rec.company_id.currency_id
            amt = rec.amount_total
            if rec.currency_id.id != company_curr.id:
                amt = self.pool.get('res.currency').compute(self.cr, self.uid, rec.currency_id.id, company_curr.id, rec.amount_total, context=self.context)
            self.sheet.write(i, 11, rec.residual)

            kplus = now - last_payment
            if kplus.days > 0:
                self.sheet.write(i, 12, kplus.days)
            else:
                self.sheet.write(i, 12, '-')


            i += 1

        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp