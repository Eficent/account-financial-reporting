# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Tax Report',
    'version': '12.0.1.0.0',
    'category': 'Reporting',
    'author': 'ForgeFlow,'
              'Odoo Community Association (OCA)',
    "website": "https://odoo-community.org/",
    'depends': [
        'account_financial_report',
    ],
    'data': [
        'wizard/tax_report_wizard_view.xml',
        'menuitems.xml',
        'reports.xml',
        'report/templates/layouts.xml',
        'report/templates/open_items.xml',
        'view/report_template.xml',
        'view/report_tax_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
