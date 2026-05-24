# order-service



## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./orders.db` | Database connection string |
| `PRODUCT_SERVICE_URL` | `http://product:8080/products/{id_product}` | Product service URL |
| `EXCHANGE_SERVICE_URL` | `http://exchange:8080/exchanges/{from_currency}/{to_currency}` | Exchange service URL |

## Run with Docker

```bash
docker build -t projetomicro/order:latest .
docker-compose up
```

The service runs on `http://localhost:8080`.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --app-dir app --host 0.0.0.0 --port 8080 --reload
```

## Test with curl

Create order:
```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -H "id-account: user-1" \
  -d '{"items": [{"idProduct": "abc-123", "quantity": 2}]}'
```

List orders:
```bash
curl http://localhost:8080/orders \
  -H "id-account: user-1"
```

Get order by id:
```bash
curl http://localhost:8080/orders/{id} \
  -H "id-account: user-1"
```

Get order by id with currency conversion:
```bash
curl "http://localhost:8080/orders/{id}?currency=BRL" \
  -H "id-account: user-1"
```

## Swagger

```
http://localhost:8080/docs
```

## Metrics

```
http://localhost:8080/metrics
```