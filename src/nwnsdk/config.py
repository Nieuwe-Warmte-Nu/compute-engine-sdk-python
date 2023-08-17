from dataclasses import dataclass
from enum import Enum


class WorkFlowType(Enum):
    GROWTH_OPTIMIZER = 'growth_optimizer'

@dataclass
class PostgresConfig:
    host: str
    port: int
    database_name: str
    user_name: str
    password: str


@dataclass
class RabbitmqConfig:
    host: str
    port: int
    exchange_name: str
    user_name: str
    password: str
    hipe_compile: int | None = 1
