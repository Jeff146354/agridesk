"""
Domain-level exceptions for Agridesk.

Each exception carries a machine-readable ``code`` and a human-readable
``message``.  The global exception handler in ``main.py`` maps these to
structured JSON responses and appropriate HTTP status codes.
"""

from __future__ import annotations


class AgrideskError(Exception):
    """Base exception for all Agridesk domain errors."""

    def __init__(self, message: str, code: str = "AGRIDESK_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(AgrideskError):
    """Raised when a requested entity does not exist."""

    def __init__(self, message: str = "Entity tidak ditemukan"):
        super().__init__(message, code="ENTITY_NOT_FOUND")


class InvalidStateTransitionError(AgrideskError):
    """Raised when a state transition violates the workflow rules."""

    def __init__(self, message: str = "Transisi status tidak valid"):
        super().__init__(message, code="INVALID_STATE_TRANSITION")


class UnauthorizedError(AgrideskError):
    """Raised when the actor lacks permission for the operation."""

    def __init__(self, message: str = "Akses ditolak"):
        super().__init__(message, code="UNAUTHORIZED")


class ValidationError(AgrideskError):
    """Raised when input data fails domain validation."""

    def __init__(self, message: str = "Validasi gagal"):
        super().__init__(message, code="VALIDATION_ERROR")


class DuplicateEntityError(AgrideskError):
    """Raised when a unique constraint would be violated."""

    def __init__(self, message: str = "Data sudah ada"):
        super().__init__(message, code="DUPLICATE_ENTITY")


class InternalError(AgrideskError):
    """Raised when an unexpected server-side error occurs."""

    def __init__(self, message: str = "Terjadi kesalahan server"):
        super().__init__(message, code="INTERNAL_ERROR")
