from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
import datetime


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields

class revenue_by_country_mtm(object):
    _name = 'sale.by.country.mtm'
    _description = "Sale By Country MTM"
    #_auto = False

    def suma(self,k,m):
        i = 0.0
        
        i = k-m
        return i

    def _var(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.act,
                obj.tar
            
                )
            res[obj.id] = su
        return res
    _columns = {
        #'partner_id': fields.many2one('res.partner', 'Customer'),
        'country_id': fields.many2one('res.country', 'Country'),
        'tar': fields.float('Target'),
        'act': fields.float('Actual'),
        'dif': fields.float('Variance'),
        }
   
    def __init__(self,cr, uid, pool, context=None):
        
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
    def generate_by_mtm(self,data):
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('AR Aging Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()
        self.header_style = xlwt.Style.easyxf('font: height 200, bold 1;')
        self.num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')

        self.sheet.write(1, 1, 'Country', self.header_style)
        self.sheet.write(1, 2, 'Actual', self.header_style)
        self.sheet.write(1, 3, 'Target', self.header_style)
        self.sheet.write(1, 4, 'Variance', self.header_style)
        i = 2
        obj = self.pool.get('location.rev')
        obj1= self.pool.get('sale.by.country.report')
        year= datetime.datetime.now().year
        mon=data[0]['mon']
        sqll=" select country_id from sale_by_country_report  where %s notnull"%(mon)
        self.cr.execute(sqll)
        co_id= [c[0] for c in self.cr.fetchall()]
        #raise ValueError, mon
        for c in co_id:

            ids = obj.search(self.cr, self.uid, [('mon','=',str(mon)),('year','=',year),('country_id','=',c)], context=self.context)
            
            if ids:
                #raise ValueError, (ids)
                rec=obj.browse(self.cr, self.uid, ids[0], context=self.context)
                sql="""
                SELECT  %s FROM sale_by_country_report where country_id =%s
                """ %(mon,rec.country_id.id)
                self.cr.execute(sql)
                act =  self.cr.fetchone()[0]
                #raise ValueError, (act,rec.tar_mo)
                dif=act-rec.tar_mo
                self.sheet.write(i, 1, rec.country_id.name)
                self.sheet.write(i, 2, act,self.num_style)
                self.sheet.write(i, 3, rec.tar_mo, self.num_style)
                self.sheet.write(i, 4, dif, self.num_style)
               
                i += 1
            else:
                sql="""
                SELECT  %s FROM sale_by_country_report where country_id =%s
                """ %(mon,c)
                self.cr.execute(sql)
                act =  self.cr.fetchone()[0]
                #raise ValueError, (act,rec.tar_mo)
                sql="""
                SELECT  name FROM res_country where id =%s
                """ %(c)
                self.cr.execute(sql)
                country_name =  self.cr.fetchone()[0]
                dif=act
                self.sheet.write(i, 1, country_name)
                self.sheet.write(i, 2, act,self.num_style)
                self.sheet.write(i, 3, 0.0, self.num_style)
                self.sheet.write(i, 4, dif, self.num_style)
               
                i += 1
                
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp            
#YTD

class revenue_by_country_ytd(object):
    _name = 'sale.by.country.ytd'
    _description = "Sale By Country YTD"
    #_auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        #'partner_id': fields.many2one('res.partner', 'Customer'),
        'country_id': fields.many2one('res.country', 'Country'),
        'tar': fields.float('Target'),
        'act': fields.float('Actual'),
        'dif': fields.float('Variance'),
        }
   
    def __init__(self,cr, uid, pool, context=None):
        
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
    def generate_by_ytd(self,data):
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Revenue YTD Vs Target Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()
        self.header_style = xlwt.Style.easyxf('font: height 200, bold 1;')
        self.num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')

        self.sheet.write(1, 1, 'Country', self.header_style)
        self.sheet.write(1, 2, 'YTD Actual', self.header_style)
        self.sheet.write(1, 3, 'YTD Target', self.header_style)
        self.sheet.write(1, 4, 'Variance', self.header_style)
        ##
        i=2
        obj = self.pool.get('location.rev')
        year= datetime.datetime.now().year
        sqll=" select country_id from sale_by_country_report "
        self.cr.execute(sqll)
        co_id= [c[0] for c in self.cr.fetchall()]
        #raise ValueError, mon
        for c in co_id:

            ids = obj.search(self.cr, self.uid, [('year','=',year),('country_id','=',c)], context=self.context)
            
            if ids:
                #raise ValueError, (ids)
                rec=obj.browse(self.cr, self.uid, ids[0], context=self.context)
                sql="""
                SELECT  COALESCE(q1,0) FROM sale_by_country_report where country_id =%s
                """ %(rec.country_id.id)
                self.cr.execute(sql)
                act1 =  self.cr.fetchone()[0]

                sql1="""
                SELECT  COALESCE(q2,0) FROM sale_by_country_report where country_id =%s
                """ %(rec.country_id.id)
                self.cr.execute(sql1)
                act2 =  self.cr.fetchone()[0]

                sql2="""
                SELECT  COALESCE(q3,0) FROM sale_by_country_report where country_id =%s
                """ %(rec.country_id.id)
              
                self.cr.execute(sql2)
                act3 =  self.cr.fetchone()[0]
                #raise ValueError, (act3,act2,act1)

                act =self.suma(act1,act2,act3)

                sqlt="""
                SELECT  sum(tar_mo) FROM location_rev where country_id =%s and year=%s
                """ %(rec.country_id.id,year)
              
                self.cr.execute(sqlt)
                tar=self.cr.fetchone()[0]
                #raise ValueError, (act,tar)
                dif=act-tar
                self.sheet.write(i, 1, rec.country_id.name)
                self.sheet.write(i, 2, act,self.num_style)
                self.sheet.write(i, 3, tar, self.num_style)
                self.sheet.write(i, 4, dif, self.num_style)
               
                i += 1
            else:
                sql="""
                SELECT  COALESCE(q1,0) FROM sale_by_country_report where country_id =%s
                """ %(c)
                self.cr.execute(sql)
                act1 =  self.cr.fetchone()[0]

                sql1="""
                SELECT  COALESCE(q2,0) FROM sale_by_country_report where country_id =%s
                """ %(c)
                self.cr.execute(sql1)
                act2 =  self.cr.fetchone()[0]

                sql2="""
                SELECT  COALESCE(q3,0) FROM sale_by_country_report where country_id =%s
                """ %(c)
              
                self.cr.execute(sql2)
                act3 =  self.cr.fetchone()[0]
                act =self.suma(act1,act2,act3)

                #raise ValueError, (act3,act2,act1)
               
                act =self.suma(act1,act2,act3)
                
                sql="""
                SELECT  name FROM res_country where id =%s
                """ %(c)
                self.cr.execute(sql)
                country_name =  self.cr.fetchone()[0]
                dif=act
                self.sheet.write(i, 1, country_name)
                self.sheet.write(i, 2, act,self.num_style)
                self.sheet.write(i, 3, 0.0, self.num_style)
                self.sheet.write(i, 4, dif, self.num_style)
               
                i += 1
        ##
       
                #cou_id.append(rec.country_id.id)
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp            
