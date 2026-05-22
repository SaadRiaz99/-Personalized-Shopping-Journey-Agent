# Collaboration Guide: Future Updates

This document outlines the workflow for when other team members complete their agents.

## 1. Integrating New Agents
When a team member provides a new agent (e.g., a "Payment Agent" or "Size Recommender"):
1.  **Orchestrator Update:** I will import the new agent into `boutiqueOrchestrator.js` and add a new method call in the `recommendItems` or a new transaction flow.
2.  **Guardrail Update:** I will update `privacyGuardrail.js` to define what data the new agent is allowed to see. For example, a Payment Agent would need "Financial Data" consent, which we will add to the `consents` object.

## 2. Maintenance Plan
- **Orchestrator:** Keep the logic lean. The Orchestrator should only manage the *sequence* of events.
- **Guardrail:** Any new external API call introduced by team members MUST be registered in the Guardrail's `validateRequest` method to prevent accidental PII leaks.

## 3. Communication
Team members should provide:
- The agent's class/module.
- A list of data inputs required.
- Any specific privacy concerns related to their agent's functionality.
