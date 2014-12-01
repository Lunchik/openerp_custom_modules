class ap_aging_cache(osv.osv):
    _name = 'ap.aging.cache'
    _description = "AP Aging Report"
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

    def initfa(self, cr,data):
        tools.sql.drop_view_if_exists(cr, 'ap_aging_cache')
        #raise ValueError (data[0]['company_id'][0])
        com_id=data[0]['company_ids']
        #com_id=tuple(com_id)
        #raise ValueError (com_id)

        cr.execute("""
            CREATE OR REPLACE VIEW  ap_aging_cache as (


                   select ROW_NUMBER() OVER() as id, (select name from res_partner where id=o.partner_id) as partner,

                        (select name from res_country where id=(select country_id from res_partner where id=o.partner_id)) as country,
                        currency_id,
                    (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 0 and (now()::date - a.date_invoice) <= 30 and
                     a.partner_id=o.partner_id) as "a0_30",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 31 and (now()::date - a.date_invoice) <= 60 and
                     a.partner_id=o.partner_id) as "a31_60",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 61 and (now()::date - a.date_invoice) <= 90 and
                     a.partner_id=o.partner_id) as "a61_90",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 91 and (now()::date - a.date_invoice) <= 120 and
                     a.partner_id=o.partner_id) as "a91_120",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 121 and (now()::date - a.date_invoice) <= 150 and
                     a.partner_id=o.partner_id) as "a121_150",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 151 and (now()::date - a.date_invoice) <= 365 and
                     a.partner_id=o.partner_id) as "a151_365",

                     (select sum(a.amount_total) from account_invoice a where  a.type='in_invoice' and a.state = 'open' and
                    (now()::date - a.date_invoice) >= 366 and (now()::date - a.date_invoice) <= 547 and
                     a.partner_id=o.partner_id) as "a366_547"

                    from account_invoice o where type='in_invoice' and o.state = 'open' and company_id in %s
                    group by partner_id, currency_id

                    order by partner_id
                )""", (tuple(com_id),))


ap_aging_cache()

class APAgingReport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context

        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('AP Aging Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def generate(self):

        self.sheet.write(0, 1, 'Supplier Name', self.style)
        self.sheet.write(0, 2, 'Country', self.style)
        self.sheet.write(0, 3, 'Remaining Amount USD', self.style)
        self.sheet.write(0, 4, '0-30', self.style)
        self.sheet.write(0, 5, '31-60', self.style)
        self.sheet.write(0, 6, '61-90', self.style)
        self.sheet.write(0, 7, '91-120', self.style)
        self.sheet.write(0, 8, '121-150', self.style)
        self.sheet.write(0, 9, '151-365', self.style)
        self.sheet.write(0, 10, '366-547', self.style)

        sobj = self.pool.get('ap.aging.cache')
        sobj.initfa(self.cr,self.data)
        ids = sobj.search(self.cr, self.uid, [], context=self.context)

        records = sobj.browse(self.cr, self.uid, ids, context=self.context)

        i = 1

        for rec in records:
            summ = self.suma(rec.a0_30,
                rec.a31_60,
                rec.a61_90,
                rec.a91_120,
                rec.a121_150,
                rec.a151_365,
                rec.a366_547)
            self.sheet.write(i, 1, rec.partner)
            self.sheet.write(i, 2, rec.country)
            self.sheet.write(i, 3, rec.total)
            self.sheet.write(i, 4, rec.a0_30 or '-')
            self.sheet.write(i, 5, rec.a31_60 or '-')
            self.sheet.write(i, 6, rec.a61_90 or '-')
            self.sheet.write(i, 7, rec.a91_120 or '-')
            self.sheet.write(i, 8, rec.a121_150 or '-')
            self.sheet.write(i, 9, rec.a151_365 or '-')
            self.sheet.write(i, 10, rec.a366_547 or '-')

            i += 1

        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp