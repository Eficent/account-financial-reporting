# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import time

class TaxReportWizard(models.TransientModel):
    """Tax report wizard."""

    _name = "tax.report.wizard"
    _description = "Tax Report Wizard"
    _inherit = 'account_financial_report_abstract_wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    date_from = fields.Date(required=True,
                            default=lambda self: self._init_date_from())
    date_to = fields.Date(required=True,
                          default=fields.Date.context_today)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
        domain=[('reconcile', '=', True)],
        required=True,
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
        default=lambda self: self._default_partners(),
    )
    account_code_from = fields.Many2one(
        comodel_name='account.account',
        string='Account Code From',
        help='Starting account in a range')
    account_code_to = fields.Many2one(
        comodel_name='account.account',
        string='Account Code To',
        help='Ending account in a range')

    def _init_date_from(self):
        """set start date to begin of current year if fiscal year running"""
        today = fields.Date.context_today(self)
        cur_month = fields.Date.from_string(today).month
        cur_day = fields.Date.from_string(today).day
        last_fsc_month = self.env.user.company_id.fiscalyear_last_month
        last_fsc_day = self.env.user.company_id.fiscalyear_last_day

        if cur_month < last_fsc_month \
                or cur_month == last_fsc_month and cur_day <= last_fsc_day:
            return time.strftime('%Y-01-01')

    @api.onchange('account_code_from', 'account_code_to')
    def on_change_account_range(self):
        if self.account_code_from and self.account_code_from.code.isdigit() and \
            self.account_code_to and self.account_code_to.code.isdigit():
            start_range = int(self.account_code_from.code)
            end_range = int(self.account_code_to.code)
            self.account_ids = self.env['account.account'].search([
                ('code', 'in', [
                    x for x in range(start_range, end_range + 1)]),
                ('user_type_id.internal_group', 'in', ('income', 'expense'))
            ])
            if self.company_id:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id)
        return {'domain': {
            'account_code_from': [('user_type_id.internal_group', 'in',
                                   ('income', 'expense'))],
            'account_code_to': [('user_type_id.internal_group', 'in',
                                 ('income', 'expense'))]
        }}

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Handle company change."""
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or
                not p.company_id)
        if self.company_id and self.account_ids:
            if self.receivable_accounts_only or self.payable_accounts_only:
                self.onchange_type_accounts_only()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id)
        res = {'domain': {'account_ids': [],
                          'partner_ids': []}}
        if not self.company_id:
            return res
        else:
            res['domain']['account_ids'] += [
                ('company_id', '=', self.company_id.id)]
            res['domain']['partner_ids'] += self._get_partner_ids_domain()
        return res

    @api.onchange('account_ids')
    def onchange_account_ids(self):
        return {'domain': {'account_ids': [('user_type_id.internal_group',
                                            'in', ('income', 'expense'))]}}

    @api.multi
    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_tax_report()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_tax_report_xlsx'
        else:
            report_name = 'account_tax_report.tax_report'
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1).report_action(
            self, data=data)

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        report_type = 'qweb-html'
        return self._export(report_type)

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_tax_report(self):
        self.ensure_one()
        return {
            'wizard_id': self.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'company_id': self.company_id.id,
            'target_move': self.target_move,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids or [],
        }

    def _export(self, report_type):
        return self._print_report(report_type)
