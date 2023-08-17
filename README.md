# Compute engine sdk python
Nieuwe Warmte Nu


## install/update pip package
see
https://packaging.python.org/en/latest/tutorials/packaging-projects/#:~:text=Generating%20distribution%20archives

## usage
Install in development mode, in root directory:
```
pip install -e .
```

or install from pypi:
```
pip install nwnsdk
```

Start local rabbitmq and postgres, in root directory:
```
docker-compose up
```

Example usage
```python
from uuid import uuid4
from nwnsdk import NwnClient, WorkFlowType, PostgresConfig, RabbitmqConfig

postgres_config = PostgresConfig(
    "localhost",
    5432,
    "nieuwewarmtenu",
    "root",
    "1234",
)
rabbitmq_config = RabbitmqConfig(
    "localhost",
    5672,
    "nwn",
    "root",
    "5678",
)
nwn_client = NwnClient(postgres_config, rabbitmq_config)
job_id: uuid4 = nwn_client.start_work_flow(WorkFlowType.GROWTH_OPTIMIZER, "test_job", "esdl_string", "test_user")

print(job_id)
```