from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

class assetlocationsumaryreport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Assets Tool Fleet Summary')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()
    
 
    def generate(self):

        self.sheet.write(1, 1, 'Asset Name ', self.style)
        lopj= self.pool.get('tgt.location')
        sobj = self.pool.get('account.asset.asset')
        acobj = self.pool.get('account.asset.category')
        ids = sobj.search(self.cr, self.uid, [], context=self.context)
        assets = sobj.browse(self.cr, self.uid, ids, context=self.context)

        locts = []
        assetcatog = []


        for asset in assets:
            if asset.location.id not in locts:
                if asset.location.id:
                    locts.append(asset.location.id)
            if asset.child_category.id not in assetcatog:
                if asset.child_category.id:
                    assetcatog.append(asset.child_category.id)
        #raise ValueError, repr(locts)

        ids = locts
        locations=lopj.browse(self.cr, self.uid, ids, context=self.context)

        j=2
        for location in locations:
            loid=location.id
            self.sheet.write(1, j, location.name, self.style)
            j += 1

        self.sheet.write(1, j, 'Total',self.style)
            

        ids = assetcatog
        assetscatogres = acobj.browse(self.cr, self.uid, ids, context=self.context)
        i=2
        for cat in assetscatogres:
            totalasset= 0
            self.sheet.write(i,1 ,cat.name)
            z=2
            for loct_id in locts:
                assetall =0
                assets = sobj.search(self.cr, self.uid, [('location','=',loct_id),('child_category','=',cat.id)], context=self.context)
                assetall = len(assets)
                self.sheet.write(i, z, assetall)
                totalasset = assetall + totalasset
                z += 1
            self.sheet.write(i, z, totalasset)

            i += 1

        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

