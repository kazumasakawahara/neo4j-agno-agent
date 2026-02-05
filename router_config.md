# Router Configuration
This file defines the routing logic for the Distributor Agent.

## Agents

### 1. WATCHDOG (Emergency)
- **Role**: Immediate life safety and critical incident response.
- **Triggers**:
    - "Unconscious", "Collapsed", "Seizure" (loss of consciousness)
    - "Bleeding", "Injury", "Accident"
    - "Missing Person" (elopement)
    - "Violence" *with immediate physical danger*
- **Excluded**:
    - "Panic" (unless danger is imminent) -> CLINICAL
    - "Bad mood" -> CLINICAL
    - "Refusal" -> CLINICAL

### 2. CLINICAL (Behavioral Advisor)
- **Role**: Specialized advice for behavioral issues and known conditions.
- **Triggers**:
    - "Panic", "Meltdown", "Crying"
    - "Refusal" (refusing bath, food, etc.)
    - "Self-harm" (minor/repetitive), "Hitting" (behavioral expression)
    - "Obsession", "Repetitive behavior"
    - Questions about "How to handle..." or "Why is he..."

### 3. SUPPORT (General Planner)
- **Role**: Routine support, logging, and general questions.
- **Triggers**:
    - "Log this...", "Record updated"
    - "Contact info for..." (unless context implies emergency, then still Support can handle info retrieval)
    - "Plan for tomorrow"
    - "Finding a hospital" (non-emergency)
    - Greetings, small talk

## Conflict Resolution
- If **Emergency** is suspected but ambiguous, prefer **WATCHDOG**.
- If **Behavioral** vs **General**, prefer **CLINICAL** if it involves specific symptoms.
