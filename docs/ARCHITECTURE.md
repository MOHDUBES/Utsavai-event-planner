# UtsavAI Architecture Documentation

This folder contains architecture diagrams and additional documentation.

## System Architecture

See README.md in the root for the full Mermaid architecture diagram.

## Budget Engine Formula

```
BudgetAllocation = BasePct(EventType) × PriorityBoost × CityMultiplier × SeasonMultiplier
```

## Timeline Milestones

| Milestone | Days Before | Notes |
|---|---|---|
| Venue booking | T-90 to T-240 | Depends on event type |
| Caterer confirmation | T-60 | After venue |
| Invitations sent | T-30 to T-60 | Printed + digital |
| Final headcount | T-14 | For caterer |
| Vendor confirmations | T-3 | Advance payments |
| Day-of coordination | T-0 | All hands on deck |
