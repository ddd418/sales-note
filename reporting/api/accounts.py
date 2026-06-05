"""Account and customer JSON APIs.

This module is the domain entry point for account/customer API routes. The
remaining implementation is delegated to the legacy view module while the large
``reporting.views`` file is split in phases.
"""

from reporting.views import (  # noqa: F401
    account_cleanup_account_search_api,
    account_contact_save_api,
    account_delivery_records_xlsx_export_api,
    account_detail_summary_api,
    account_update_api,
    companies_management_api,
    company_create_api,
    company_delete_api,
    company_update_api,
    customer_delete_api,
    customer_delivery_records_xlsx_export_api,
    customer_detail_summary_api,
    customer_update_api,
    customers_summary_api,
    department_create_api,
    department_delete_api,
    department_update_api,
)
