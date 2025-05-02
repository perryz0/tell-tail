# TellTail Webhook Integration

This module provides webhook functionality to integrate TellTail with CI/CD infrastructure and other external systems.

## Features

- Webhook triggers for ACL changes (add, remove, update)
- Event-based architecture with structured payloads
- Integration with the ACL manager for automatic triggering

## Usage

### Environment Configuration

Set the `TELLTAIL_WEBHOOK_URL` environment variable to enable actual webhook HTTP requests:

```bash
export TELLTAIL_WEBHOOK_URL="https://your-webhook-endpoint.com/hook"
```

### Supported Events

The following webhook events are supported:

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `acl.user.added` | User added to ACL | A new user is added to the ACL |
| `acl.user.removed` | User removed from ACL | A user is removed from the ACL |
| `acl.user.updated` | User ACL updated | A user's port permissions are changed |

### Webhook Payload Structure

Webhook payloads follow this general structure:

```json
{
  "event_type": "acl.user.added",
  "payload": {
    "operation": "add",
    "username": "user123",
    "ports": ["22/tcp", "80/tcp"],
    "tailnet": "example.com",
    "success": true
  }
}
```

## Development

To trigger webhooks manually or for testing:

```python
from services.hooks.webhooks import trigger_webhook

# Example payload
payload = {
    "operation": "test",
    "username": "testuser",
    "ports": ["22/tcp"],
    "tailnet": "example.com",
    "success": True
}

# Trigger the webhook
trigger_webhook("acl.test", payload)
```

### Testing

Run the webhook integration test to verify functionality:

```bash
python test_webhook_integration.py
``` 