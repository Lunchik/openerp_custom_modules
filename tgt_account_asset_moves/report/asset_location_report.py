from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

class assetlocationreport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Assets Tool fleet (location)')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def generate(self):

        self.sheet.write(2, 1, 'Asset Name ', self.style)
        self.sheet.write(2, 2, 'Gross Value', self.style)
        self.sheet.write(2, 3, 'Residual Value', self.style)
        self.sheet.write(2, 4, 'Currency', self.style)
        assetcatog = []


        sobj = self.pool.get('account.asset.asset')
        acobj = self.pool.get('account.asset.category')
        location = self.data.get('location_id')[1]

        self.sheet.write(0, 1, 'location : ', self.style)        
        self.sheet.write(0, 2, location)
    
        ids = sobj.search(self.cr, self.uid, [('location','in',[self.data.get('location_id')[0]]),], context=self.context)
        assets = sobj.browse(self.cr, self.uid, ids, context=self.context)
        for catog in assets:
            if catog.child_category.id not in assetcatog: 
                if catog.child_category.id:
                    assetcatog.append(catog.child_category.id)

            #assetcatog.remove(False)
        ids = assetcatog
        #raise ValueError, repr(ids)
        assetscatogres = acobj.browse(self.cr, self.uid, ids, context=self.context)

        i = 3
        for cat in assetscatogres:
            child_category = cat.id
            pur_vall =vall_re  =0
            self.sheet.write(i, 1, cat.name)
            #raise ValueError, repr(assets)
            #for asset in assets:

              #  if child_category == asset.child_category:
               #     pur_vall = pur_vall + asset.purchase_value
               #     vall_re = vall_re + asset.value_residual
               # namcur = asset.currency_id.name
            ids = sobj.search(self.cr, self.uid, [('location','in',[self.data.get('location_id')[0]]),('child_category','=',cat.id)], context=self.context)
            assetsall = sobj.browse(self.cr, self.uid, ids, context=self.context)
            for asset in assetsall:
                pur_vall = pur_vall + asset.purchase_value
                vall_re = vall_re + asset.value_residual
                namcur = asset.currency_id.name


            self.sheet.write(i, 2, pur_vall)
            self.sheet.write(i, 3, vall_re)
            self.sheet.write(i, 4, namcur)
            i += 1

        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

