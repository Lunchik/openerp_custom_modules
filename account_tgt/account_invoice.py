from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

from datetime import datetime
class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'company_id': fields.many2one('res.company', 'TGT Entity', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
        'date_invoice': fields.date('Invoice Date', readonly=True, states={'draft':[('readonly',False)]}, select=True, help="Keep empty to use the current date"),
        'con':fields.related('partner_id', 'country_id',type="many2one",relation="res.country",string="Country",store=False),

    }

    def onchange_company_id(self, cr, uid, ids, company_id, part_id, type, invoice_line, currency_id):
        result = super(account_invoice, self).onchange_company_id(cr, uid, ids, company_id, False, type, invoice_line, currency_id)
        type2account = {'out_invoice': 'receivable', 'in_invoice': 'payable'}
        result['domain']['account_id'] = [('company_id', '=', company_id), ('type', '=', type2account.get(type, 'receivable'))]
        result['value']['account_id'] = False
        #raise ValueError, result
        return result

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        company_id = invoice_browse.company_id.id
        lines = []
        for l in move_lines:
            line = l[2]
            line['company_id'] = company_id
            lines.append((0, 0, line))
        return lines
    def namount_line (self,cr,uid,ids,context=None):
        
        idss=self.search(cr,uid,[],context=context)
        for rec in self.browse(cr,uid,idss,context=context):
            self.namount_line1(cr,uid,[rec.id],context=context)
    def namount_line1(self,cr,uid,ids,context=None):
        bro=self.pool.get('account.invoice.line')
        idss=bro.search(cr,uid,[('invoice_id', '=', ids[0])],context=context)
        f=bro.nnamount_line(cr,uid,idss,ids[0],context=context)
        #raise ValueError, idss
        #return f
    def countxy(self,cr,uid,ids,context=None):

        y=0
        x=0
        county=0
        countx=0
        cur=self.browse(cr, uid, ids[0]).currency_id
        date=self.browse(cr, uid, ids[0]).date_invoice
        #raise ValueError, self.browse(cr, uid, ids[0]).invoice_line
        #raise ValueError, self.browse(cr, uid, ids[0]).id

        for line in self.browse(cr, uid, ids[0]).invoice_line:

            if line.product_id.job_cat == 'other':
                y+=line.price_subtotal
                county+=1
            else:
                x+=line.price_subtotal
                countx+=1

        return y,x,countx,county,cur,date
class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'

  
    def nnamount_line(self, cr, uid, ids,invoice_id, context=None):
        res = {}
       
        y=0
        x=0
        county=0
        countx=0
        

        bro=self.pool.get('account.invoice')
        y,x,countx,county,cur,date=bro.countxy(cr,uid,[invoice_id],context=None)
       # raise ValueError, str(date)
        sql="select rate from res_currency_rate where currency_id=%s and to_char(name::date,'mm-yyyy')=to_char('%s'::date,'mm-yyyy')"
        cr.execute(sql % (cur.id, date))
        rate=cr.fetchone()
        if rate is not None:  # or just "if row"
            rate = rate[0]
        else:
            rate=1
        #raise ValueError, (rate,cur.id,date)
        if cur.id==3:
            
            for line in self.browse(cr, uid, ids):
                if y != 0 and x !=0 :
                    ids=line.id
                    if line.product_id.job_cat == 'other':

                        price_nsubtotal= line.price_subtotal
                        self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)

                    else:

                        price_nsubtotal= (line.price_subtotal+((line.price_subtotal/x)*y))
                        #raise ValueError,[price_nsubtotal]
                        self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)


             
                else:
                    price_nsubtotal= line.price_subtotal  
                    #raise ValueError,'[price_nsubtotal]'

                    self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)

            #res[line.id] = price_nsubtotal
            print "IDS",price_nsubtotal
            print "ID",line.id
        else:

            for line in self.browse(cr, uid, ids):
                if y != 0 and x !=0 :
                    ids=line.id
                    if line.product_id.job_cat == 'other':

                        price_nsubtotal= line.price_subtotal*rate
                        self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)

                    else:

                        price_nsubtotal= (line.price_subtotal*rate+(((line.price_subtotal*rate)/x)*y))
                        #raise ValueError,[price_nsubtotal]
                        self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)


                 
                else:
                    price_nsubtotal= line.price_subtotal*rate
                    

                    self.write(cr,uid,[line.id], {'price_nsubtotal':price_nsubtotal},context=context)

                #res[line.id] = price_nsubtotal
                print "IDS",price_nsubtotal
                print "ID",line.id

                

            return True
    
    _columns = {
        'price_nsubtotal': fields.float('New Amount'),
        #'price_nsubtotal': fields.function(nnamount_line, string='nAmount', type="float",
            #digits_compute= dp.get_precision('Account'), store=True),
        }