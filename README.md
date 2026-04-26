# StatusInsights
Ta 在干什么？

## Dashboard

Open the dashboard at `/` to view the name, person status, and device statuses.
It auto-refreshes every 5 seconds using `/status/summary`.

## API Key Authentication

Set the API key in your environment and pass it via request header.

```
export STATUSINSIGHTS_API_KEY="your-secret"
```

Example request:

```
curl -H "X-API-Key: your-secret" http://127.0.0.1:8000/device/get
```
