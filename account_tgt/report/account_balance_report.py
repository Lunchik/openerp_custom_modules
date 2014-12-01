from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64


from .base_accounting_report import CombinedReport

class Dummy(object):
    name = '-'

class TrialBalanceReport(CombinedReport):

    def __init__(self, cr, uid, pool, name, context={}):
        super(TrialBalanceReport, self).__init__(cr, uid, pool, name, context=context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.result_acc = []

    def get_fiscalyears(self, fiscal_id, company_ids, period_ids):
        # NOTE: don't forget AND company_id in %company_ids
        self.cr.execute("""
            SELECT f.id FROM account_fiscalyear f WHERE
            f.company_id IN %s AND
             f.date_start=(SELECT date_start FROM account_fiscalyear WHERE id=%s) 
            AND f.date_stop=(SELECT date_stop FROM account_fiscalyear WHERE id=%s)
            """, (tuple(company_ids), fiscal_id, fiscal_id))
        fiscals = [id[0] for id in self.cr.fetchall()]
        if not period_ids:
            self.cr.execute("""
                SELECT p.id FROM account_period p WHERE
                 p.fiscalyear_id IN %s AND
                 p.special = %s

                  ORDER BY p.code
                """, (tuple(fiscals), False))
            period_ids = [id[0] for id in self.cr.fetchall()]
            self.cr.execute("""
                SELECT p.id FROM account_period p WHERE
                 p.fiscalyear_id IN %s AND
                 p.special = %s

                  ORDER BY p.code
                """, (tuple(fiscals), True))
            openperiods = [id[0] for id in self.cr.fetchall()]            
        return (fiscals, period_ids, openperiods)


    def get_periods(self, period_from, period_to, company_ids):
        # NOTE: don't forget AND company_id in %company_ids
        self.cr.execute("""
            SELECT p.id FROM account_period p WHERE
             p.company_id IN %s AND
             p.special = %s AND
             p.date_start>=(SELECT date_start FROM account_period WHERE id=%s) AND 

              p.date_stop<=(SELECT date_stop FROM account_period WHERE id=%s)

              ORDER BY p.code
            """, (tuple(company_ids), False, period_from, period_to))
        periods = [id[0] for id in self.cr.fetchall()]

        self.cr.execute("""
            SELECT p.id, p.code FROM account_period p WHERE 
            p.special = false AND
            p.date_stop < (SELECT date_start FROM account_period WHERE id=%s)
            AND p.date_start >= (
            SELECT f.date_start FROM account_fiscalyear f WHERE
             f.id=(SELECT fiscalyear_id FROM account_period WHERE id=%s)
            )

            AND p.company_id IN %s

              ORDER BY p.code
            """, ( period_from, period_from, tuple(company_ids),))

        open_periods = [id[0] for id in self.cr.fetchall()]
        return (periods, open_periods)

    def summation(self, lines):
        ret = {
            'credit': 0.0,
            'debit': 0.0,
            'balance': 0.0,
            'initial_balance': 0.0,
            'cost_centre': '',
        }
        for rline in lines:
            #bolder = styles[6]
            #i += 1
            #self.sheet.write(i, 3, rline.analytic_account_id.name, bolder)
            #self.sheet.write(i, 4, rline.name, bolder)
            #bolder = styles[7]
            blc = getattr(rline, 'balance', rline.debit - rline.credit)
            lll = rline.debit - rline.credit
            #self.sheet.write(i, 5, 0.0, bolder)
            #self.sheet.write(i, 6, rline.debit, bolder)
            ret['debit'] += rline.debit
            ret['credit'] += rline.credit
            ret['balance'] += lll
            ret['cost_centre'] = rline.analytic_account_id.name
            #self.sheet.write(i, 7, rline.credit, bolder)
            #self.sheet.write(i, 8, lll, bolder)

        return ret

    def generate(self):
        account_obj = self.pool.get('account.account')
        analytic_obj = self.pool.get('account.analytic.account')
        self.sheet.write(0, 1, 'Code', self.style)
        self.sheet.write(0, 2, 'Account Name', self.style)
        self.sheet.write(0, 3, 'Cost Centre', self.style)
        self.sheet.write(0, 4, 'Description', self.style)
        self.sheet.write(0, 5, 'Opening Balance', self.style)
        self.sheet.write(0, 6, 'Debit', self.style)
        self.sheet.write(0, 7, 'Credit', self.style)
        self.sheet.write(0, 8, 'Ending Balance', self.style)

        # Account Type Bolding

        styles = {
            0: xlwt.Style.easyxf('font: height 230, bold 1;', num_format_str='#,##0.00'),
            1: xlwt.Style.easyxf('font: height 200, bold 1, color green;', num_format_str='#,##0.00'),
            2: xlwt.Style.easyxf('font: height 190, bold 1, color green;', num_format_str='#,##0.00'),
            3: xlwt.Style.easyxf('font: height 180, bold 1, color green;', num_format_str='#,##0.00'),
            4: xlwt.Style.easyxf('font: height 170, bold 1, color green;', num_format_str='#,##0.00'),
            5: xlwt.Style.easyxf('font: height 160, bold 0, color green;', num_format_str='#,##0.00'),
            6: xlwt.Style.easyxf('font: height 190, bold 0;', num_format_str='#,##0.00'),
            7: xlwt.Style.easyxf('font: height 190, bold 0;', num_format_str='#,##0.00'),
        }

        i = 2
        all_ids, heavy = self.all_lines(self.data)
        for meta in all_ids:
            bolder = styles[3]
            line = heavy[meta]
            account = account_obj.browse(self.cr, self.uid, meta, context=self.context)
            if not line:
                continue
            for aid, drcr in line.iteritems():
                analytic = Dummy()
                if aid != 0:
                    analytic = analytic_obj.browse(self.cr, self.uid, aid, context=self.context)

                self.sheet.write(i, 1, account.code, bolder)
                self.sheet.write(i, 2, account.name, bolder)
                self.sheet.write(i, 3, analytic.name, bolder)
                self.sheet.write(i, 5, drcr[0][2], bolder)
                self.sheet.write(i, 6, drcr[0][0], bolder)
                self.sheet.write(i, 7, drcr[0][1], bolder)
                self.sheet.write(i, 8, (drcr[0][0] - drcr[0][1]) - drcr[0][2], bolder)
                i += 1
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

    def set_context(self, objects, data, ids, report_type=None):
        self.ids = ids
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
            self.ids = new_ids
        return super(TrialBalanceReport, self).set_context(objects, data, new_ids, report_type=report_type)

    #def _add_header(self, node, header=1):
    #    if header == 0:
    #        self.rml_header = ""
    #    return True

    def _get_account(self, data):
        if data['model']=='account.account':
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['id']).company_id.name
        return super(TrialBalanceReport ,self)._get_account(data)

    def all_lines(self, form, ids=None, done=None):
        #raise ValueError, form
        form = form['form']
        period_ids, openperiods = [], []
        date_from, date_to, open_date_from, open_date_to = '', '', '', ''
        ctx = self.context.copy()

        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['company_ids'] = form['company_ids']
        if form['filter'] == 'filter_period':
            ctx['period_from'] = form['period_from']
            ctx['period_to'] = form['period_to']
            #raise ValueError , ctx['period_to']
            period_ids, openperiods = self.get_periods(ctx['period_from'], ctx['period_to'], ctx['company_ids'])
        elif form['filter'] == 'filter_date':
            ctx['date_from'] = form['date_from']
            ctx['date_to'] =  form['date_to']
            date_from, date_to = ctx['date_from'], ctx['date_to']
            odf, odt = datetime.strptime(ctx['date_from'], '%Y-%m-%d'), datetime.strptime(ctx['date_to'], '%Y-%m-%d')
            open_date_from, open_date_to = datetime(odf.year, 1, 1), odf - timedelta(days=1)
        ctx['state'] = form['target_move']

        if not period_ids:
            fiscalyear_ids, period_ids, openperiods = self.get_fiscalyears(ctx['fiscalyear'], ctx['company_ids'], period_ids)

        
        
        all_res = {}

        # NOTE: don't forget AND company_id in %company_ids
        self.cr.execute("""
            SELECT a.id FROM account_account a WHERE type != 'view' AND company_id IN %s
            GROUP BY a.id, a.code, a.name
            ORDER BY a.code
            """, (tuple(ctx['company_ids']), ))

        all_ids = [id[0] for id in self.cr.fetchall()]

        for acc_id in all_ids:
            plug = ''
            plug2 = ''
            if ctx['state'] == 'posted':
                plug = """
                    AND (SELECT state FROM account_move WHERE id=m.move_id)='posted'
                """
                plug2 = """
                    AND (SELECT state FROM account_move m WHERE m.id=move_id)='posted'
                """
            SQL = """
                (SELECT m.id FROM account_move_line m WHERE m.account_id=%s {})
            """.format(plug)
            # get all analytic lines
            self.cr.execute("""
                SELECT account_id, SUM(amount) as total FROM account_analytic_line WHERE general_account_id=%s
                AND move_id IN 
                {}
                GROUP BY account_id
                """.format(SQL), (acc_id, acc_id))
            analytic_lines = [id for id in self.cr.fetchall()]
            # NOTE: don't forget AND period_id IN ()
            if not date_from:
                self.cr.execute("""
                    SELECT account_id, SUM(debit) as dr, SUM(credit) as cr FROM account_move_line WHERE account_id=%s AND period_id IN %s {}
                    GROUP BY account_id
                    """.format(plug2), (acc_id, tuple(period_ids)))
            else:
                self.cr.execute("""
                    SELECT account_id, SUM(debit) as dr, SUM(credit) as cr FROM account_move_line WHERE account_id=%s AND period_id IN %s AND date_created BETWEEN %s AND %s {}
                    GROUP BY account_id
                    """.format(plug2), (acc_id, tuple(period_ids), date_from, date_to))
            lines = self.cr.fetchall()
            # NOTE: don't forget AND period_id IN ()
            #cr.execute("""
            #    SELECT id FROM account_move_line WHERE account_id=%s
            #    """, (acc_id, ))
            # NOTE: don't forget AND period_id IN ()
            if not date_from:
                self.cr.execute("""
                    SELECT move_id, account_id, SUM(amount) as total FROM account_analytic_line WHERE general_account_id=%s AND move_id IN 
                    (SELECT m.id FROM account_move_line m WHERE m.account_id=%s AND period_id IN %s {})
                    GROUP BY account_id, move_id
                    ORDER BY move_id
                    """.format(plug), (acc_id, acc_id, tuple(period_ids)))
            else:
                self.cr.execute("""
                    SELECT move_id, account_id, SUM(amount) as total FROM account_analytic_line WHERE general_account_id=%s AND move_id IN 
                    (SELECT m.id FROM account_move_line m WHERE m.account_id=%s AND period_id IN %s AND date_created BETWEEN %s AND %s {})
                    GROUP BY account_id, move_id
                    ORDER BY move_id
                    """.format(plug), (acc_id, acc_id, tuple(period_ids), date_from, date_to))
            move_analytics = self.cr.fetchall()
            m = {}
            for m_id, aacc_id, amt in move_analytics:
                if m.get(aacc_id, None):
                    m[aacc_id].append(m_id)
                else:
                    m[aacc_id] = [m_id]

            one_res = {}
            total_dr, total_cr = 0.0, 0.0

            # OPEN BALANCES

            # NOTE: don't forget AND period_id IN ()
            if not date_from and openperiods:
                self.cr.execute("""
                    SELECT account_id, SUM(debit) as dr, SUM(credit) as cr FROM account_move_line WHERE account_id=%s AND period_id IN %s {}
                    GROUP BY account_id
                    """.format(plug2), (acc_id, tuple(openperiods)))
            elif openperiods and date_from:
                self.cr.execute("""
                    SELECT account_id, SUM(debit) as dr, SUM(credit) as cr FROM account_move_line WHERE account_id=%s AND period_id IN %s AND date_created BETWEEN %s AND %s {}
                    GROUP BY account_id
                    """.format(plug2), (acc_id, tuple(openperiods), open_date_from, open_date_to))
            openlines = openperiods and self.cr.fetchall() or []
            # NOTE: don't forget AND period_id IN ()
            #cr.execute("""
            #    SELECT id FROM account_move_line WHERE account_id=%s
            #    """, (acc_id, ))
            # NOTE: don't forget AND period_id IN ()
            if not date_from and openperiods:
                self.cr.execute("""
                    SELECT move_id, account_id, SUM(amount) as total FROM account_analytic_line WHERE general_account_id=%s AND move_id IN 
                    (SELECT m.id FROM account_move_line m WHERE m.account_id=%s AND period_id IN %s {})
                    GROUP BY account_id, move_id
                    ORDER BY move_id
                    """.format(plug), (acc_id, acc_id, tuple(openperiods)))
            elif openperiods and date_from:
                self.cr.execute("""
                    SELECT move_id, account_id, SUM(amount) as total FROM account_analytic_line WHERE general_account_id=%s AND move_id IN 
                    (SELECT m.id FROM account_move_line m WHERE m.account_id=%s AND period_id IN %s AND date_created BETWEEN %s AND %s {})
                    GROUP BY account_id, move_id
                    ORDER BY move_id
                    """.format(plug), (acc_id, acc_id, tuple(openperiods), open_date_from, open_date_to))
            open_move_analytics = openperiods and self.cr.fetchall() or []
            om = {}
            for m_id, aacc_id, amt in open_move_analytics:
                if om.get(aacc_id, None):
                    om[aacc_id].append(m_id)
                else:
                    om[aacc_id] = [m_id]

            #one_res = {}
            ototal_dr, ototal_cr, obalance = 0.0, 0.0, 0.0


            # ENDE OPEN PERIODS
            # ENDE OPEN BALANCES
            for a_id, ids in m.iteritems():
                # NOTE: don't forget AND period_id IN ()
                self.cr.execute("""
                SELECT SUM(debit) as dr, SUM(credit) as cr FROM account_move_line WHERE account_id=%s AND id IN %s
                """, (acc_id, tuple(ids),))
                res = self.cr.fetchall()
                res = [[s[0], s[1], 0.0] for s in res]
                oids = []
                oids = om.get(a_id, [])
                if oids:
                    self.cr.execute("""
                    SELECT SUM(debit) - SUM(credit) FROM account_move_line WHERE account_id=%s AND id IN %s
                    """, (acc_id, tuple(oids),))
                    ores = [float(k[0]) for k in self.cr.fetchall()][0]
                    res[0][2] += ores
                    obalance += ores


                total_dr += float(res[0][0])
                total_cr += float(res[0][1])
                one_res[a_id] = res
            if lines:
                no_analytics_dr = float(lines[0][1]) - total_dr
                no_analytics_cr = float(lines[0][2]) - total_cr
                ono_analytics = 0.0
                if openlines:
                    ono_analytics = (float(openlines[0][1]) - float(openlines[0][2])) - obalance
                no_analytics = [(no_analytics_dr, no_analytics_cr, ono_analytics)]
                one_res[0] = no_analytics
                #raise ValueError, (acc_id, one_res)
            all_res[acc_id] = one_res

        return (all_ids, all_res)
