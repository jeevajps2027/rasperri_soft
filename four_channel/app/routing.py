from django.urls import re_path
from app.consumers import SerialConsumer,KeypadConsumer,LEDConsumer

websocket_urlpatterns = [
    re_path(r'ws/comport/$', SerialConsumer.as_asgi()),
    re_path(r'ws/measurement/$', SerialConsumer.as_asgi()),
    re_path(r'ws/keypad/$', KeypadConsumer.as_asgi()),
     re_path(r'ws/led/$', LEDConsumer.as_asgi()),  # 👈 Add this
]