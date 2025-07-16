#app/channels/__init__.py

from socketio import Server, RedisManager

from app.channels.connection import Connection
from configs.settings import ALLOWED_HOSTS

origins = len(ALLOWED_HOSTS) and ','.join([f'http://{host},https://{host}' for host in ALLOWED_HOSTS]).split(',') or []
cors_allowed_origins = '*' in ALLOWED_HOSTS and '*' or origins
client_manager = RedisManager('redis://127.0.0.1:6379/1', write_only=True)
io = Server(cors_allowed_origins=cors_allowed_origins, client_manager=client_manager, async_mode='eventlet')

io.register_namespace(Connection('/'))
