"""
Database module for Facility Intelligence Copilot.

This module re-exports the database session objects from session.py
for backward compatibility with main.py and other modules.
"""

from app.db.session import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
