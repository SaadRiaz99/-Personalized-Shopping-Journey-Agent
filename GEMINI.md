# Personalized Shopping Journey Agent

## Architecture
The system is designed as a multi-agent orchestration to provide a high-end, personalized shopping experience while maintaining strict privacy standards.

### Agents
1.  **Boutique Orchestrator:** Manages the overall shopping journey.
2.  **Style Profiler:** Analyzes user preferences and style.
3.  **Discovery Agent:** Finds products across the web.
4.  **Privacy Guardrail Agent:** Ensures compliance and protects user data.

## Privacy Guardrail Agent (PGA)
The PGA acts as a middleware between the user's private data and the external world (Retailers/LLMs).

### Core Responsibilities
- **Data Minimization:** Only pass the necessary attributes to external APIs.
- **Consent Management:** Verify consent before accessing sensitive data (e.g., location, biometric data).
- **Compliance:** Implement GDPR/CCPA logic (Right to Access, Right to Erasure).
- **Anonymization:** Strip PII from outbound requests.
