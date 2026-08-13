"""Vercel serverless entry point (WSGI bridge for the FastAPI app)."""

from a2wsgi import ASGIMiddleware

from api.main import app

handler = ASGIMiddleware(app)
