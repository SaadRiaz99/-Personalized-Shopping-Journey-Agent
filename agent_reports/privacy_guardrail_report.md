# Privacy Guardrail — Individual Test Report
**Date:** 2026-06-02 09:20:40
**Passed:** 23 | **Failed:** 0 | **Total:** 23

## Results
| Test Case | Status | Detail |
|---|---|---|
| no_pii_passes | PASS |  |
| email_redacted_strict | PASS |  |
| phone_redacted_strict | PASS |  |
| ssn_redacted_strict | PASS |  |
| multiple_pii_redacted | PASS |  |
| empty_text | PASS |  |
| whitespace_text | PASS |  |
| agent_access_strict_blocks | PASS |  |
| agent_access_open_allows | PASS |  |
| agent_access_balanced_blocks_phone | PASS |  |
| agent_access_balanced_allows_email | PASS |  |
| output_strict_blocks_personal_data | PASS |  |
| output_strict_allows_safe | PASS |  |
| output_balanced_blocks_precise_location | PASS |  |
| gdpr_forget_user | PASS |  |
| gdpr_forget_nonexistent | PASS |  |
| export_profile | PASS |  |
| export_profile_not_found | PASS |  |
| ccpa_opt_out | PASS |  |
| rule_based_redact_email | PASS |  |
| rule_based_redact_phone | PASS |  |
| rule_based_redact_ssn | PASS |  |
| rule_based_redact_clean | PASS |  |