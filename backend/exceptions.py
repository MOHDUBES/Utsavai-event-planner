"""
Custom exception hierarchy for UtsavAI backend.
"""

from __future__ import annotations


class UtsavAIException(Exception):
    """Base exception for all UtsavAI errors."""


class PlanningEngineException(UtsavAIException):
    """Raised when an error occurs during deterministic event planning."""


class InvalidEventParameterError(PlanningEngineException):
    """Raised when event input values violate business logic constraints."""


class BudgetCalculationError(PlanningEngineException):
    """Raised when budget allocation cannot satisfy minimum constraints."""


class ChatServiceError(UtsavAIException):
    """Raised when the conversational assistant fails to interpret or update a plan."""


class AIProviderError(UtsavAIException):
    """Raised when an external LLM provider call fails or times out."""
