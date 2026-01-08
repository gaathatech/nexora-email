from flask_sqlalchemy import SQLAlchemy

# SocketIO is optional in the runtime environment. If not installed,
# we'll set `socketio` to None so imports succeed during development/tests.
try:
    from flask_socketio import SocketIO
    socketio = SocketIO()
except Exception:
    socketio = None

db = SQLAlchemy()
