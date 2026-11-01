from app.main import create_app

app = create_app()
# Vercel passes the original path, /api included, and the routes are declared without it.
app.root_path = "/api"
