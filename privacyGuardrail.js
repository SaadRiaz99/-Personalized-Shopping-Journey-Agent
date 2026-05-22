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
        this.consents = userPreferences.consents || {
            marketing: false,
            thirdPartySharing: false,
            biometricData: false
        };
    }

    /**
     * GDPR: Right to Erasure
     */
    forgetUser() {
        console.log('Privacy Guardrail: Executing "Right to Erasure". Purging all local PII...');
        this.consents = {};
        return true;
    }

    /**
     * Updates consent for a specific category.
     */
    updateConsent(category, value) {
        if (this.consents.hasOwnProperty(category)) {
            this.consents[category] = value;
            return true;
        }
        return false;
    }

    /**
     * Filters out sensitive data based on privacy levels and explicit consents.
     */
    validateRequest(agentName, dataRequest) {
        const filteredData = { ...dataRequest };
        const sensitiveFields = ['email', 'phone', 'precise_location', 'realName'];

        // Apply Privacy Level Restrictions
        if (this.privacyLevel === PrivacyLevel.STRICT) {
            sensitiveFields.forEach(field => delete filteredData[field]);
            if (filteredData.location) filteredData.location = 'Anonymized Region';
        } else if (this.privacyLevel === PrivacyLevel.BALANCED) {
            if (filteredData.email) filteredData.email = 'masked@example.com';
            if (filteredData.phone) filteredData.phone = 'XXX-XXX-XXXX';
        }

        // Apply Granular Consent Checks
        if (!this.consents.thirdPartySharing) {
            delete filteredData.external_id;
        }

        return filteredData;
    }

    /**
     * Check if an action is compliant.
     */
    checkCompliance(action, laws = ['GDPR', 'CCPA']) {
        if (action === 'share_with_third_party' && !this.consents.thirdPartySharing) {
            return false;
        }
        if (action === 'marketing_email' && !this.consents.marketing) {
            return false;
        }
        return true;
    }
}

module.exports = { PrivacyGuardrailAgent, PrivacyLevel };
