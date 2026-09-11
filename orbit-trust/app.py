"""Vercel Python Function entrypoint (doc 04): exports the FastAPI instance."""

from orbit_trust.api import app

__all__ = ["app"]
