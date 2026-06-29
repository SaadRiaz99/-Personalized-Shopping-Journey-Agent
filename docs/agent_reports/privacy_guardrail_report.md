# Privacy Guardrail — Individual Test Report
**Date:** 2026-06-29 10:57:14
**Passed:** 56 | **Failed:** 4 | **Total:** 60

## Results
| Test Case | Status | Detail |
|---|---|---|
| no_pii | PASS |  |
| email_strict | PASS |  |
| phone_strict | PASS |  |
| ssn_strict | PASS |  |
| address_strict | PASS |  |
| cc_strict | PASS |  |
| multi_pii | PASS |  |
| email_domain | PASS |  |
| phone_intl | PASS |  |
| single_name | PASS |  |
| empty_strict | PASS |  |
| whitespace_strict | PASS |  |
| email_balanced | PASS |  |
| phone_balanced | PASS |  |
| access_strict_blocks | PASS |  |
| access_strict_public | PASS |  |
| access_open | PASS |  |
| access_open_no_consent | PASS |  |
| access_balanced_phone | PASS |  |
| access_balanced_email | PASS |  |
| access_strict_ssn | PASS |  |
| access_strict_cc | PASS |  |
| access_balanced_location | PASS |  |
| access_strict_name | PASS |  |
| access_analytics_noshare | PASS |  |
| output_strict_loc | PASS |  |
| output_strict_name | PASS |  |
| output_strict_inferred | PASS |  |
| output_strict_safe | PASS |  |
| output_balanced_loc | PASS |  |
| output_balanced_safe | PASS |  |
| output_empty | PASS |  |
| output_no_profile | PASS |  |
| gdpr_forget | PASS |  |
| gdpr_forget_nonexist | PASS |  |
| export_profile | PASS |  |
| export_not_found | PASS |  |
| ccpa_opt_out | PASS |  |
| update_consent | PASS |  |
| delete_profile | PASS |  |
| delete_nonexist | PASS |  |
| access_search_noconsent | PASS |  |
| access_custom | PASS |  |
| rule_redact_email | PASS |  |
| rule_redact_phone | PASS |  |
| rule_redact_ssn | PASS |  |
| rule_redact_address | PASS |  |
| rule_redact_cc | PASS |  |
| rule_redact_clean | PASS |  |
| rule_redact_multi_phone | FAIL |  |
| rule_redact_safe_num | PASS |  |
| rule_redact_email_plus | PASS |  |
| rule_redact_cc_spaces | PASS |  |
| rule_redact_street | PASS |  |
| rule_redact_drive | PASS |  |
| output_strict_combined | PASS |  |
| output_nonexistent_user | PASS |  |
| input_guardrail_disabled | FAIL |  |
| access_guardrail_disabled | FAIL |  |
| output_guardrail_disabled | FAIL |  |