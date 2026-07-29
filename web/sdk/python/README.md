# GBT Python SDK

Python client for the [gbtxiaotudou.com](https://gbtxiaotudou.com) API.

## Install

```bash
pip install gbt-sdk
```

## Quick Start

```python
from gbt_sdk import GBT

client = GBT(api_key="gbt_xxxxx")

# Create a checkout session
checkout = client.checkout_configurations.create(
    plan={"initial_price": 10.0, "plan_type": "one_time"},
    metadata={"order_id": "order_123"},
)
print(checkout.id)

# List projects
for project in client.projects.list():
    print(project.name, project.price)

# List payments
for payment in client.payments.list(status="completed"):
    print(payment.amount, payment.coin)

# Create deployment
deploy = client.deployments.create(
    repo_url="https://github.com/user/repo",
    plan="basic",
)
print(deploy.status)
```

## API

### Checkout Configurations
- `client.checkout_configurations.create(plan, *, metadata, success_url, cancel_url, idempotency_key)`
- `client.checkout_configurations.retrieve(checkout_id)`

### Payments
- `client.payments.list(*, limit, cursor, status)`
- `client.payments.retrieve(payment_id)`

### Projects
- `client.projects.list(*, limit, cursor, category)`
- `client.projects.retrieve(project_id)`

### Deployments
- `client.deployments.create(repo_url, *, plan, env_vars, branch, build_command, idempotency_key)`
- `client.deployments.retrieve(deployment_id)`
- `client.deployments.status(deployment_id)`

## Errors

All SDK errors inherit from `GBTError`:

| Exception | Status |
|---|---|
| `GBTError` | Base |
| `APIConnectionError` | Network |
| `AuthenticationError` | 401 |
| `NotFoundError` | 404 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |

## License

MIT
