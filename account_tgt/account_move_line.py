from openerp.osv import osv, fields

# Reversing Transactions.

class account_move(osv.osv):

    _inherit = 'account.move'

    def action_reverse_tranaction(self, cr, uid, ids, context=None):

        if not ids:
            return False

        ids = ids[0]

        move = self.browse(cr, uid, ids, context=context)

        data = {
            'name': '%s/REV' % move.name,
            'narration': move.narration,
            'company_id': move.company_id.id,
            'date': move.date,
            'ref': '%s/REV' % move.ref,
            'journal_id': move.journal_id.id,
            'period_id': move.period_id.id,
        }

        lines = []

        for line in move.line_id:
            dc_line = {
                'company_id': line.company_id.id,
                'name': line.name,
                'date': line.date,
                'partner_id': line.partner_id and line.partner_id.id or False,
                'account_id': line.account_id.id,
                'journal_id': line.journal_id.id,
                'period_id': line.period_id.id,
                'debit': line.credit,
                'credit': line.debit,
                #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                'analytic_account_id': line.analytic_account_id and line.analytic_account_id.id or False,
                'tax_code_id': line.tax_code_id and line.tax_code_id.id or False,
                'tax_amount': line.tax_amount,
                'amount_currency': -1 * line.amount_currency,
                'currency_id': line.currency_id and line.currency_id.id or False,
            }

            lines.append((0, 0, dc_line))

        data['line_id'] = lines

        move_id = self.create(cr, uid, data, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move_id,
            'view_mode': 'form',
            'name': 'Reversed Trasaction [%s]' % move.ref,
        }