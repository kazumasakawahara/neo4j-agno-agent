---
name: sos_orchestrator
description: Intelligent agent that orchestrates emergency response based on context (Medical vs Behavioral).
---

# SOS Orchestrator Skill

This skill replaces the static "Blast everyone" approach with a smart decision-making process.

## Capabilities

1.  **Context Analysis**: Determines if the emergency is Medical (seizure, injury) or Behavioral (panic, wandering).
2.  **Recipient Targeting**: Selects the most appropriate responders (e.g., Doctor for Medical, Helper for Behavioral).
3.  **Message Personalization**: Includes relevant data (medications vs calming techniques) in the alert.

## Scripts

- `smart_sos.py`: Main script to decide the SOS content and recipients.

## Usage

```bash
# Run Smart SOS logic
uv run python skills/sos_orchestrator/smart_sos.py "Client Name" "Situation Description"
```
