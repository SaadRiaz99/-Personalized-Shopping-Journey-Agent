# Project Report: Personalized Shopping Journey Agent System

## 1. Project Overview
This project implements a multi-agent AI system designed to provide a personalized, high-end shopping experience while strictly adhering to modern privacy standards (GDPR/CCPA). The system acts as a "Digital Personal Shopper" that understands user style, budget, and dislikes while acting as a protective barrier for their personal data.

## 2. System Architecture
The system follows a modular orchestration pattern, where specialized agents communicate through a central coordinator.

### A. Boutique Orchestrator (The Brain)
- **Role:** Coordinates the workflow between the user and other agents.
- **Function:** Ensures every request passes through the Privacy Guardrail before reaching external sources.

### B. Privacy Guardrail Agent (The Shield)
- **Role:** Ensures data minimization and legal compliance.
- **Key Features:**
  - Supports multiple privacy levels (Strict, Balanced, Open).
  - Handles granular consent management (e.g., opting out of marketing).
  - Implements the "Right to Erasure" (Forget Me) feature.

### C. Style Profiler Agent (The Stylist)
- **Role:** Analyzes user preferences to curate recommendations.
- **Key Features:**
  - Positive matching (Brand, Color, Budget).
  - **Negative Preferences:** Automatically filters out "disliked" attributes (e.g., certain colors or brands).
  - Scoring engine that ranks products by relevancy.

### D. Discovery Agent (The Researcher)
- **Role:** Searches for products across a variety of retailers.
- **Function:** Normalizes data from different sources into a consistent format for scoring.

## 3. Technical Implementation
- **Language:** Node.js (JavaScript)
- **Design Pattern:** Object-Oriented Agent Orchestration.
- **Privacy First:** The system is built so that PII (Personally Identifiable Information) never leaves the local environment unless explicit consent is given.

## 4. Conclusion
The prototype successfully demonstrates that AI personalization does not have to come at the cost of user privacy. By using a dedicated Privacy Guardrail, we can leverage powerful recommendation engines while keeping the user in full control of their data.
