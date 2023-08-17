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

from nwnsdk.nwn_client import NwnClient

rabbitmq_client = NwnClient('localhost')
job_id: uuid4 = rabbitmq_client.start_work_flow('growth_optimizer', 'test_job', 'esdl_string', 'test_user')

print(job_id)
```