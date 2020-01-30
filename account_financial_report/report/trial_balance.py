#
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

class TrialBalanceReport(models.AbstractModel):
    _name = 'report.account_financial_report.trial_balance'


    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext.update(context.get('data'))
        active_id = context.get('active_id')
        wiz = self.env['open.items.report.wizard'].browse(active_id)
        rcontext['o'] = wiz
        result['html'] = self.env.ref(
            'account_financial_report.report_trial_balance').render(rcontext)
        return result

    def _get_trial_balance_data(self, account):
        return {
            'id': account.id,
            'name': account.name,
            'code': account.code,
            'currency_id': account.currency_id,
            'currency_name':account.currency_id.name,
            'debit': 0.0,
            'credit': 0.0,
            'initial_balance':0.0,
            'balance':0.0,
            'final_balance':0.0,
            'hide_line': False,
        }


    def _get_trial_balance_domain(self, wizard, account_ids, company):
        domain = []

        if company:
            domain += [('company_id', '=', company.id)]
        if account_ids:
            domain += [('id', 'in', account_ids)]
        return domain

    def _get_trial_balance(self, wizard, account_ids, company,
                           show_partner_details,partner_ids):
        accounts = self.env['account.account'].search(
            self._get_trial_balance_domain(wizard, account_ids, company),
            order='name asc')
        trial_balance_data = []
        for account in accounts:
            trial_balance_data.append(
                self._get_trial_balance_data(account))
        return trial_balance_data



    def _get_moves_domain(self, wizard, journal_ids):
        domain = [
            ('journal_id', 'in', journal_ids),
        ]
        return domain

    def _get_moves_order(self, wizard, journal_ids):
      return ''

    def _get_moves_data(self, move):
        return {
            'move_id': move.id,
            'journal_id': move.journal_id.id,
            'entry': move.name,
        }

    def _get_moves(self, wizard, journal_ids):
        moves = self.env['account.move'].search(
            self._get_moves_domain(wizard, journal_ids),
            order=self._get_moves_order(wizard, journal_ids))
        Moves = []
        move_data = {}
        for move in moves:
            move_data[move.id] = self._get_moves_data(move)
            Moves.append(move_data[move.id])
        return moves.ids, Moves, move_data

    def _get_move_lines_order(self, account_ids, wizard,
                              partner_ids):
        return ''

    def _get_move_lines_domain(self, account_ids, wizard,
                               partner_ids):
        domain = []
        if account_ids:
            domain += [('account_id', 'in', account_ids)]
        if partner_ids:
            domain += [('partner_id', 'in', partner_ids)]
        return domain

    def _get_move_lines_data(self, ml, wizard):
            return {
                'move_line_id': ml.id,
                'move_id': ml.move_id.id,
                'date': ml.date,
                'journal_id': ml.journal_id.id,
                'account_id': ml.account_id.id,
                'partner_id': ml.partner_id.id,
                'label': ml.name,
                'debit': ml.debit,
                'credit': ml.credit,
                'balance':ml.balance,
                'company_currency_id': ml.company_currency_id.id,
                'amount_currency': ml.amount_currency,
                'currency_id': ml.currency_id.id,
            }

    def _get_move_lines(self, account_ids, wizard, partner_ids):
        move_lines = self.env['account.move.line'].search(
            self._get_move_lines_domain(account_ids, wizard,
                                        partner_ids),
            order=self._get_move_lines_order(account_ids, wizard,
                                             partner_ids))
        Move_Lines = {}
        accounts = self.env['account.account']
        partners = self.env['res.partner']
        currencies = self.env['res.currency']
        for ml in move_lines:
            if ml.account_id not in accounts:
                accounts |= ml.account_id
            if ml.partner_id not in partners:
                partners |= ml.partner_id
            if ml.currency_id not in currencies:
                currencies |= ml.currency_id
            if ml.move_id.id not in Move_Lines.keys():
                Move_Lines[ml.move_id.id] = []
            Move_Lines[ml.move_id.id].append(self._get_move_lines_data(
                ml, wizard))
        account_ids_data = self._get_account_data(accounts)
        partner_ids_data = self._get_partner_data(partners)
        currency_ids_data = self._get_currency_data(currencies)
        return move_lines.ids, Move_Lines, account_ids_data, \
            partner_ids_data, currency_ids_data

    def _get_account_data(self, accounts):
        data = {}
        for account in accounts:
            data[account.id] = self._get_account_id_data(account)
        return data

    def _get_account_id_data(self, account):
        return {
            'name': account.name,
            'code': account.code,
            'internal_type': account.internal_type,
        }

    def _get_partner_data(self, partners):
        data = {}
        for partner in partners:
            data[partner.id] = self._get_partner_id_data(partner)
        return data

    def _get_partner_id_data(self, partner):
        return {
            'name': partner.name,
        }

    def _get_currency_data(self, currencies):
        data = {}
        for currency in currencies:
            data[currency.id] = self._get_currency_id_data(currency)
        return data

    def _get_currency_id_data(self, currency):
        return {
            'name': currency.name,
        }



    @api.multi
    def _get_report_values(self, docids, data):
        wizard_id = data['wizard_id']
        wizard = self.env['trial.balance.report.wizard'].browse(wizard_id)
        company = self.env['res.company'].browse(data['company_id'])
        partner_ids = data['partner_ids']
        journal_ids = data['journal_ids']
        account_ids = data['account_ids']
        show_partner_details= data['show_partner_details']
        trial_balances_data=self._get_trial_balance(
            wizard, account_ids, company, show_partner_details, partner_ids)
        move_ids, moves_data, move_ids_data = self._get_moves(
            wizard, journal_ids)
        move_lines_data = account_ids_data = partner_ids_data = \
            currency_ids_data = {}
        if move_ids:
            move_line_ids, move_lines_data, account_ids_data, \
            partner_ids_data, currency_ids_data = \
                self._get_move_lines(
                account_ids, wizard, partner_ids)
        account_totals={}
        for move_id in move_lines_data.keys():
            for move_line_data in move_lines_data[move_id]:
                account_id = move_line_data['account_id']
                if account_id not in account_totals.keys():
                    account_totals[account_id] = {
                        'debit': 0.0,
                        'credit': 0.0,
                        'balance':0.0,
                        'initial_balance': 0.0,
                        'partner_totals':{},
                    }
                if wizard.date_from <= move_line_data['date'] <= wizard.date_to:
                    for item in ['debit', 'credit', 'balance']:
                        account_totals[account_id][item] += move_line_data[item]
                elif move_line_data['date'] < wizard.date_from:
                    account_totals[account_id]['initial_balance'] += \
                        move_line_data['balance']
        for trial_balance_data in trial_balances_data:
            account_id = trial_balance_data['id']
            if account_id in account_totals.keys():
                for item in ['debit', 'credit','balance','initial_balance']:
                    trial_balance_data[item] += \
                        account_totals[account_id][item]
                trial_balance_data['final_balance'] += (trial_balance_data[
                    'initial_balance']+trial_balance_data['balance'])
            if data['hide_account_at_0'] and (
                float_is_zero(trial_balance_data['initial_balance'],
                              precision_digits=2)
                and float_is_zero(trial_balance_data['final_balance'],
                                  precision_digits=2)
                and float_is_zero(trial_balance_data['debit'], precision_digits=2)
                and float_is_zero(trial_balance_data['credit'],
                                  precision_digits=2)):
                    trial_balance_data['hide_line'] = True
        trial_balances_data= [x for x in trial_balances_data if not x[
            'hide_line']]

        if show_partner_details:
            for move_id in move_lines_data.keys():
                for move_line_data in move_lines_data[move_id]:
                    account_id = move_line_data['account_id']
                    partner_id = move_line_data['partner_id']
                    if partner_id not in account_totals[account_id][
                        'partner_totals']:
                        account_totals[account_id]['partner_totals'][
                            partner_id]={
                            'partner_id':partner_id,
                            'debit': 0.0,
                            'credit': 0.0,
                            'balance': 0.0,
                            'initial_balance': 0.0,
                        }

                    if wizard.date_from <= move_line_data[
                        'date'] <= wizard.date_to:
                        for item in ['debit', 'credit', 'balance']:
                            account_totals[account_id]['partner_totals'][partner_id][item] += \
                                move_line_data[item]
                    elif move_line_data['date'] < wizard.date_from:
                        account_totals[account_id]['partner_totals'][partner_id]['initial_balance'] += \
                            move_line_data['balance']
            list_partners=[]
            for trial_balance_data in trial_balances_data:
                account_id=trial_balance_data['id']
                for key in account_totals[account_id][
                    'partner_totals']:
                    list_partners.append(account_totals[account_id][
                                             'partner_totals'][key])
                trial_balance_data.update({'partners_data': list_partners})
                list_partners=[]

        return {
            'doc_ids': [wizard_id],
            'doc_model': 'trial.balance.report.wizard',
            'docs': self.env['trial.balance.report.wizard'].browse(wizard_id),
            'foreign_currency': data['foreign_currency'],
            'company_name': company.display_name,
            'currency_name': company.currency_id.name,
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'only_posted_moves': data['only_posted_moves'],
            'hide_account_at_0': data['hide_account_at_0'],
            'show_partner_details': data['show_partner_details'],
            'limit_hierarchy_level': data['limit_hierarchy_level'],
            'Trial_Balance': trial_balances_data,
            'show_hierarchy_level': data['show_hierarchy_level'],
        }
