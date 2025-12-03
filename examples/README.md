# Examples

Runnable examples demonstrating kapso-whatsapp SDK capabilities.

## Setup

Set required environment variables:

```bash
export WHATSAPP_ACCESS_TOKEN="your_access_token"
export WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id"
export WHATSAPP_TEST_RECIPIENT="+15551234567"

# For webhook handler
export WHATSAPP_VERIFY_TOKEN="your_verify_token"
export WHATSAPP_APP_SECRET="your_app_secret"
```

## Examples

| File | Description |
|------|-------------|
| `send_messages.py` | Basic message types: text, image, location |
| `interactive_messages.py` | Buttons, lists, CTA URL buttons |
| `template_messages.py` | Template messages with parameters |
| `media_operations.py` | Upload, download, send media |
| `webhook_handler.py` | FastAPI webhook server |

## Running Examples

```bash
# Install dependencies
pip install kapso-whatsapp

# Run an example
python examples/send_messages.py

# Run webhook server
pip install fastapi uvicorn
python examples/webhook_handler.py
```

## Webhook Testing

Use ngrok to expose your local server:

```bash
ngrok http 8000
```

Then configure the webhook URL in Meta Developer Console:
`https://your-ngrok-url.ngrok.io/webhook`
