import json
from enum import Enum
from typing import Dict, Any, List

class PrivacyLevel(Enum):
    STRICT = "strict"      # No PII, no tracking
    BALANCED = "balanced"  # Pseudonymized data, limited tracking
    OPEN = "open"          # Personalized recommendations with PII consent

class PrivacyGuardrailAgent:
    def __init__(self, user_preferences: Dict[str, Any]):
        self.privacy_level = PrivacyLevel(user_preferences.get("privacy_level", "strict"))
        self.consent_log = []

    def validate_request(self, agent_name: str, data_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters out sensitive data based on privacy levels.
        """
        filtered_data = data_request.copy()
        sensitive_fields = ["email", "phone", "precise_location", "real_name"]

        if self.privacy_level == PrivacyLevel.STRICT:
            for field in sensitive_fields:
                filtered_data.pop(field, None)
            # Anonymize location to city/region level if present
            if "location" in filtered_data:
                filtered_data["location"] = "Anonymized Region"

        elif self.privacy_level == PrivacyLevel.BALANCED:
            # Mask email/phone
            if "email" in filtered_data:
                filtered_data["email"] = "masked@example.com"
            if "phone" in filtered_data:
                filtered_data["phone"] = "XXX-XXX-XXXX"

        return filtered_data

    def check_compliance(self, action: str, laws: List[str] = ["GDPR", "CCPA"]) -> bool:
        """
        Check if an action (e.g., 'store_data', 'share_with_third_party') is compliant.
        """
        # Placeholder for complex legal logic
        if action == "share_with_third_party" and self.privacy_level == PrivacyLevel.STRICT:
            return False
        return True

# Example Usage
if __name__ == "__main__":
    user_prefs = {"privacy_level": "strict"}
    pga = PrivacyGuardrailAgent(user_prefs)

    raw_request = {
        "item": "summer dress",
        "email": "user@example.com",
        "location": "123 Maple St, New York, NY",
        "budget": 200
    }

    safe_request = pga.validate_request("DiscoveryAgent", raw_request)
    print(f"Safe Request: {json.dumps(safe_request, indent=2)}")
