from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from openerp.osv import osv, fields



import xlwt
import tempfile
import base64
###Class
class sale_by_asst_cou_report(osv.osv):
    _name = 'sale.by.asst.cou.report'
    _description = "Sale By Asset/Country Report"
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
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.selection([('hpt', 'Sakmar / Geo'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('tot'),
        'janc': fields.float('Jan'),
        'febc': fields.float('Feb'),
        'marc': fields.float('Mar'),
        'q1c': fields.float('Q1'),
        'aprc': fields.float('Apr'),
        'mayc': fields.float('May'),
        'junc': fields.float('Jun'),
        'q2c': fields.float('Q2'),
        'julc': fields.float('Jul'),
        'augc': fields.float('Aug'),
        'sepc': fields.float('Sep'),
        'q3c': fields.float('Q3'),
        'octc': fields.float('Oct'),
        'novc': fields.float('Nov'),
        'desc': fields.float('Dec'),
        'q4c': fields.float('Q4'),
        'totalc': fields.float('tot'),
    }

    def init(self, cr):
       
              
        #tools.sql.drop_view_if_exists(cr, 'sale_by_asst_cou_report')
        cr.execute("""
            create or replace view sale_by_asst_cou_report as
            select 
            distinct on(k.job_cat,k.country_id)
            k.job_cat as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from avg_pa 
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)  from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)  from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from avg_pa
             where job_cat = k.job_cat 
             and k.country_id=country_id
             
            ) as total,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
              
             and mon=concat_ws('-',extract(year from now()), '01-01')::date
            ) as janc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and
              mon=concat_ws('-',extract(year from now()), '02-02')::date
            ) as febc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '03-03')::date
            ) as marc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '01-01')::date,concat_ws('-',extract(year from now()), '02-02')::date,concat_ws('-',extract(year from now()), '03-03')::date)
            ) as q1c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '04-04')::date
            ) as aprc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '05-05')::date
            ) as mayc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '06-06')::date
            ) as junc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '04-04')::date,concat_ws('-',extract(year from now()), '05-05')::date,concat_ws('-',extract(year from now()), '06-06')::date)
            ) as q2c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '07-07')::date
            ) as julc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '08-08')::date
            ) as augc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '09-09')::date
            ) as sepc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '07-07')::date,concat_ws('-',extract(year from now()), '08-08')::date,concat_ws('-',extract(year from now()), '09-09')::date)
            ) as q3c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '10-10')::date
            ) as octc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '11-11')::date
            ) as novc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '12-12')::date
            ) as desc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '10-10')::date,concat_ws('-',extract(year from now()), '11-11')::date,concat_ws('-',extract(year from now()), '12-12')::date)
            ) as q4c,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             
            ) as totalc
            
            
            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)
sale_by_asst_cou_report()


class assetutilazationreport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        self.book = xlwt.Workbook()
        #self.sheet = self.book.add_sheet('Assets Tool Fleet Summary')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()
    
    def generate(self):
        filter = self.data.get('filter_id')
        self.num_style2 = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        self.num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        self.num_style1 = xlwt.Style.easyxf('font: height 150, bold 0;', num_format_str='#,##0.00')
        self.header_style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue; align: horiz center;font: height 200, bold 1,color white;')
        self.header_style1 = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green; font: height 200, bold 1,color white;')

        sheet_name = ''
        if filter == 'all_countries':
            sheet_name = 'Assets utilazation By Reveune'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_avgass('Sale By asst/Country Report', 'sale_by_asst_cou_report','sale.by.asst.cou.report')
        if filter == 'all_countriesj':
            sheet_name = 'Assets utilazation By Job'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_avgass('Sale By asst/Country Report', 'job_by_asst_cou_report','job.by.asst.cou.report')


        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp   
    def generate_avgass(self, title_name, report_name, report_dot_name):
        
        self.sheet.write(1, 1, title_name, self.header_style)
        self.sheet.write(1, 2, 'Jan', self.header_style)
        self.sheet.write(1, 3, 'Feb', self.header_style)
        self.sheet.write(1, 4, 'Mar', self.header_style)
        self.sheet.write(1, 5, 'Q1', self.header_style)
        self.sheet.write(1, 6, 'Apr', self.header_style)
        self.sheet.write(1, 7, 'May', self.header_style)
        self.sheet.write(1, 8, 'Jun', self.header_style)
        self.sheet.write(1, 9, 'Q2', self.header_style)
        self.sheet.write(1, 10, 'Jul', self.header_style)
        self.sheet.write(1, 11, 'Aug', self.header_style)
        self.sheet.write(1, 12, 'Sep', self.header_style)
        self.sheet.write(1, 13, 'Q3', self.header_style)
        self.sheet.write(1, 14, 'Oct', self.header_style)
        self.sheet.write(1, 15, 'Nov', self.header_style)
        self.sheet.write(1, 16, 'Dec', self.header_style)
        self.sheet.write(1, 17, 'Q4', self.header_style)
        self.sheet.write(1, 18, 'Total', self.header_style)

        self.cr.execute("""
            SELECT DISTINCT defcol_two_id FROM %s
            """%(report_name))
        cat_ids = [c[0] for c in self.cr.fetchall()]

        #
        obj = self.pool.get(report_dot_name)
        #raise ValueError, obj
        i = 2
        for c in cat_ids:
            ids = obj.search(self.cr, self.uid, [('defcol_two_id', '=', c)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }
            totaly2 = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }
            cat = ''
            for rec in obj.browse(self.cr, self.uid, ids, context=self.context):
                totaly3 = {
                1: rec.janc,
                2: rec.febc,
                3: rec.marc,
                4: rec.q1c,
                5: rec.aprc,
                6: rec.mayc,
                7: rec.junc,
                8: rec.q2c,
                9: rec.julc,
                10: rec.augc,
                11:rec.sepc,
                12: rec.q3c,
                13: rec.octc,
                14: rec.novc,
                15: rec.desc,
                16: rec.q4c,
                17: rec.totalc,
               
            }
                i3=1
                if rec.defcol_one_id=='hpt':
                    fa = 'Sakmar/Geo'
                else:
                    fa = rec.defcol_one_id.upper()


                while i3 < 18:
                    if totaly3[i3]==0:
                        totaly3[i3]=1
                    i3+=1
                    cat = rec.defcol_two_id.name
                
                self.sheet.write(i, 1, fa)
                self.sheet.write(i, 2, rec.jan/totaly3[1], self.num_style1)
                totaly[1] += rec.jan
                totaly2[1] += rec.janc
                self.sheet.write(i, 3, rec.feb/totaly3[2], self.num_style1)
                totaly[2] += rec.feb
                totaly2[2] += rec.febc
                self.sheet.write(i, 4, rec.mar/totaly3[3], self.num_style1)
                totaly[3] += rec.mar
                totaly2[3] += rec.marc

                self.sheet.write(i, 5, rec.q1/totaly3[4], self.num_style1)
                totaly[4] += rec.q1
                totaly2[4] += rec.q1c

                self.sheet.write(i, 6, rec.apr/totaly3[5], self.num_style1)
                totaly[5] += rec.apr
                totaly2[5] += rec.aprc
                self.sheet.write(i, 7, rec.may/totaly3[6], self.num_style1)
                totaly[6] += rec.may
                totaly2[6] += rec.mayc
                self.sheet.write(i, 8, rec.jun/totaly3[7], self.num_style1)
                totaly[7] += rec.jun
                totaly2[7] += rec.junc
                self.sheet.write(i, 9, rec.q2/totaly3[8], self.num_style1)
                totaly[8] += rec.q2
                totaly2[8] += rec.q2c
                self.sheet.write(i, 10, rec.jul/totaly3[9], self.num_style1)
                totaly[9] += rec.jul
                totaly2[9] += rec.julc
                self.sheet.write(i, 11, rec.aug/totaly3[10], self.num_style1)
                totaly[10] += rec.aug
                totaly2[10] += rec.augc
                self.sheet.write(i, 12, rec.sep/totaly3[11], self.num_style1)
                totaly[11] += rec.sep
                totaly2[11] += rec.sepc
                self.sheet.write(i, 13, rec.q3/totaly3[12], self.num_style1)
                totaly[12] += rec.q3
                totaly2[12] += rec.q3c
                self.sheet.write(i, 14, rec.oct/totaly3[13], self.num_style1)
                totaly[13] += rec.oct
                totaly2[13] += rec.octc
                self.sheet.write(i, 15, rec.nov/totaly3[14], self.num_style1)
                totaly[14] += rec.nov
                totaly2[14] += rec.novc
                self.sheet.write(i, 16, rec.des/totaly3[15], self.num_style1)
                totaly[15] += rec.des
                totaly2[15] += rec.desc
                self.sheet.write(i, 17, rec.q4/totaly3[16], self.num_style1)
                totaly[16] += rec.q4
                totaly2[16] += rec.q4c
                self.sheet.write(i, 18, rec.total/totaly3[17], self.num_style1)
                totaly[17] += rec.total
                totaly2[17] += rec.totalc
                i += 1
            i1=1
            while i1 < 18:
                if totaly2[i1]==0:
                    totaly2[i1]=1
                i1+=1

            self.sheet.write(i, 1, cat, self.num_style)
            self.sheet.write(i, 2, totaly[1]/totaly2[1], self.num_style)
            self.sheet.write(i, 3, totaly[2]/totaly2[2], self.num_style)
            self.sheet.write(i, 4, totaly[3]/totaly2[3], self.num_style)
            self.sheet.write(i, 5, totaly[4]/totaly2[4], self.num_style)
            self.sheet.write(i, 6, totaly[5]/totaly2[5], self.num_style)
            self.sheet.write(i, 7, totaly[6]/totaly2[6], self.num_style)
            self.sheet.write(i, 8, totaly[7]/totaly2[7], self.num_style)
            self.sheet.write(i, 9, totaly[8]/totaly2[8], self.num_style)
            self.sheet.write(i, 10, totaly[9]/totaly2[9], self.header_style)
            self.sheet.write(i, 11, totaly[10]/totaly2[10], self.num_style)
            self.sheet.write(i, 12, totaly[11]/totaly2[11], self.num_style)
            self.sheet.write(i, 13, totaly[12]/totaly2[12], self.num_style)
            self.sheet.write(i, 14, totaly[13]/totaly2[13], self.num_style)
            self.sheet.write(i, 15, totaly[14]/totaly2[14], self.num_style)
            self.sheet.write(i, 16, totaly[15]/totaly2[15], self.num_style)
            self.sheet.write(i, 17, totaly[16]/totaly2[16], self.num_style)
            self.sheet.write(i, 18, totaly[17]/totaly2[17], self.num_style)

            i += 1
