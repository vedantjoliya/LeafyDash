import sys
import os

# Ensure the project root (one level up from api/) is on sys.path
# so that "from backend.main import app" resolves correctly on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
