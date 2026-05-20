/**
 * Privacy Guardrail Agent (PGA)
 * Ensures user data privacy and compliance (GDPR/CCPA).
 */

const PrivacyLevel = {
    STRICT: 'strict',      // No PII, no tracking
    BALANCED: 'balanced',  // Pseudonymized data, limited tracking
    OPEN: 'open'           // Personalized recommendations with PII consent
};

class PrivacyGuardrailAgent {
    constructor(userPreferences) {
        this.privacyLevel = userPreferences.privacyLevel || PrivacyLevel.STRICT;
    }

    /**
     * Filters out sensitive data based on privacy levels.
     */
    validateRequest(agentName, dataRequest) {
        const filteredData = { ...dataRequest };
        const sensitiveFields = ['email', 'phone', 'precise_location', 'realName'];

        if (this.privacyLevel === PrivacyLevel.STRICT) {
            sensitiveFields.forEach(field => delete filteredData[field]);
            // Anonymize location
            if (filteredData.location) {
                filteredData.location = 'Anonymized Region';
            }
        } else if (this.privacyLevel === PrivacyLevel.BALANCED) {
            if (filteredData.email) filteredData.email = 'masked@example.com';
            if (filteredData.phone) filteredData.phone = 'XXX-XXX-XXXX';
        }

        return filteredData;
    }

    /**
     * Check if an action is compliant.
     */
    checkCompliance(action, laws = ['GDPR', 'CCPA']) {
        if (action === 'share_with_third_party' && this.privacyLevel === PrivacyLevel.STRICT) {
            return false;
        }
        return true;
    }
}

module.exports = { PrivacyGuardrailAgent, PrivacyLevel };
