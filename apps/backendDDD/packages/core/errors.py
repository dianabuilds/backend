from __future__ import annotations


class AppError(Exception):
    pass


class NotFound(AppError):
    pass


class Conflict(AppError):
    pass


class PolicyDenied(AppError):
    pass
