from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

class assetreport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Assets report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def generate(self):

        self.sheet.write(0, 1, 'Asset Name ', self.style)
        self.sheet.write(0, 2, 'Asset Category ', self.style)
        self.sheet.write(0, 3, 'Reference ', self.style)
        self.sheet.write(0, 4, 'Asset Current Location', self.style)
        self.sheet.write(0, 5, 'Purchase Date ', self.style)
        self.sheet.write(0, 6, 'Partner', self.style)
        self.sheet.write(0, 7, 'Gross Value', self.style)
        self.sheet.write(0, 8, 'Residual Value', self.style)
        self.sheet.write(0, 9, 'Currency', self.style)
        self.sheet.write(0, 10, 'Company', self.style)
        self.sheet.write(0, 11, 'Status', self.style)

        sobj = self.pool.get('account.asset.asset')

        filte = self.data.get('filter_id')
        
        #if filte == 'comp':
        ids = sobj.search(self.cr, self.uid, [('company_id','in',self.data.get('company_ids'))], context=self.context)

        assets = sobj.browse(self.cr, self.uid, ids, context=self.context)

        i = 1
        for asset in assets:

            self.sheet.write(i, 1, asset.name)
            self.sheet.write(i, 2, asset.category_id.name)
            self.sheet.write(i, 3, asset.code)
            self.sheet.write(i, 4, asset.location.name)
            self.sheet.write(i, 5, asset.purchase_date)
            self.sheet.write(i, 6, asset.partner_id.name)
            self.sheet.write(i, 7, asset.purchase_value)
            self.sheet.write(i, 8, asset.value_residual)
            self.sheet.write(i, 9, asset.currency_id.name)
            self.sheet.write(i, 10, asset.company_id.name)
            self.sheet.write(i, 11, asset.state)
            i += 1
            '''else: 
                                                        ids = sobj.search(self.cr, self.uid ,[], context=self.context)
                                    
                                                        assets = sobj.browse(self.cr, self.uid, ids, context=self.context)
                                    
                                                        i = 1
                                                        for asset in assets:
                                    
                                                            self.sheet.write(i, 1, asset.name)
                                                            self.sheet.write(i, 2, asset.category_id.name)
                                                            self.sheet.write(i, 3, asset.code)
                                                            self.sheet.write(i, 4, asset.location.name)
                                                            self.sheet.write(i, 5, asset.purchase_date)
                                                            self.sheet.write(i, 6, asset.partner_id.name)
                                                            self.sheet.write(i, 7, asset.purchase_value)
                                                            self.sheet.write(i, 8, asset.value_residual)
                                                            self.sheet.write(i, 9, asset.currency_id.name)
                                                            self.sheet.write(i, 10, asset.company_id.name)
                                                            self.sheet.write(i, 11, asset.state)
                                                            i += 1
                                    '''
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

