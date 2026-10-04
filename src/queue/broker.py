from faststream.rabbit import RabbitBroker
from yarl import URL

from src.config.config import settings

amqp_url = URL.build(
    scheme="amqp",
    user=settings.rabbit_user,
    password=settings.rabbit_password,
    host=settings.rabbit_host,
    port=settings.rabbit_port,
)

broker = RabbitBroker(str(amqp_url))
