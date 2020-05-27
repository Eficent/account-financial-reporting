# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from odoo.tools import float_is_zero
from datetime import date, datetime
import operator


class TaxReport(models.AbstractModel):
    _name = 'report.account_tax_report.tax_report'
    _description = "Tax Report"

    @api.model
    def _get_move_line_data(self, move_line):
        move_line_data = {move_line['move_id'][0]: {
            'id': move_line['id'],
            'date': move_line['date'],
            'move': move_line['move_id'][1],
            'move_id': move_line['move_id'][0],
            'partner_id': move_line['partner_id'][0] if
            move_line['partner_id'] else False,
            'partner_name': move_line['partner_id'][1] if
            move_line['partner_id'] else "",
            'tax_ids': move_line['tax_ids'],
            'debit': move_line['debit'],
            'credit': move_line['credit'],
            'balance': move_line['balance']
            }
        }
        return move_line_data

    @api.model
    def _get_move_lines_domain(self, company_id, account_ids, partner_ids,
                               only_posted_moves, date_to, date_from):
        accounts_domain = [
            ('company_id', '=', company_id),
            ('user_type_id.internal_group', 'in', ('income', 'expense'))]
        if account_ids:
            accounts_domain += [('id', 'in', account_ids)]
        accounts = self.env['account.account'].search(accounts_domain)

        domain = [('company_id', '=', company_id),
                  ('date', '>=', date_from),
                  ('date', '<=', date_to),
                  ('account_id', 'in', accounts.ids)]
        if partner_ids:
            domain += [('partner_id', 'in', partner_ids)]
        if only_posted_moves:
            domain += [('move_id.state', '=', 'posted')]
        return domain

    def _get_data(self, account_ids, partner_ids, date_to, date_from,
                  only_posted_moves, company_id):
        domain = self._get_move_lines_domain(
            company_id, account_ids, partner_ids, only_posted_moves,
            date_to, date_from
        )
        ml_fields = [
            'id', 'name', 'date', 'move_id', 'partner_id', 'balace', 'debit',
            'credit', 'tax_line_id', 'tax_ids'
        ]
        move_lines = self.env['account.move.line'].search_read(
            domain=domain, fields=ml_fields
        )
        move_lines_data = []
        for move_line in move_lines:
            move_lines_data += [self._get_move_line_data(move_line)]




    @api.multi
    def _get_report_values(self, docids, data):
        wizard_id = data['wizard_id']
        company = self.env['res.company'].browse(data['company_id'])
        company_id = data['company_id']
        account_ids = data['account_ids']
        partner_ids = data['partner_ids']
        date_to = data['date_to']
        date_from = data['date_from']
        only_posted_moves = data['only_posted_moves']

        x = self._get_data(account_ids, partner_ids, date_to, date_from,
                           only_posted_moves, company_id)
