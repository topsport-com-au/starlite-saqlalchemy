"""Static file service configuration for the application."""
from pathlib import Path

from starlite.config import StaticFilesConfig

from starlite_saqlalchemy.constants import STATIC_DIR, STATIC_PATH

here = Path(__file__).parent


config = StaticFilesConfig(directories=[here / STATIC_DIR], path=STATIC_PATH)
