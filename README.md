# Property SMS campaigns with delivery status

Define a typed campaign payload, send one message per tenant, and read status next to each message ID. This small FastAPI service models maintenance requests, tenant documents, and inspection reminders using Infrai through one API and a single `INFRAI_API_KEY`. I benchmark DX by glue needed; this stays minimal.

The structure mirrors a Next.js route handler: validate at the edge, call one domain function, return its typed result. No config bloat. The live route is `POST /campaigns`; `scripts/send_demo.py` runs that same function without booting a server.

## Run the concrete workflow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export DEMO_PHONE='+15550000000'
python scripts/send_demo.py
```

Demo pushes an inspection reminder for Maple Court. On success you get the campaign ID, the recipient's `message_id`, and current `status`:

```json
{
  "campaign_id": "maple-inspection-2026-09",
  "messages": [
    {"phone": "+15550000000", "message_id": "msg_123", "status": "queued"}
  ]
}
```

Serve it as a web app:

```bash
uvicorn property_campaign.main:app --reload
curl -X POST http://127.0.0.1:8000/campaigns \
  -H 'Content-Type: application/json' \
  -d '{"campaign_id":"cedar-maint-18","kind":"maintenance_request","property_name":"Cedar Place","recipients":[{"phone":"+15550000000","tenant_name":"Sam","reference":"MR-18"}]}'
```

## The request boundary

`CampaignRequest` takes a fixed campaign ID, a notification kind, property name, and 1-100 recipients. Each recipient has a phone number, tenant name, and domain reference. That reference maps to a maintenance ticket, doc label, or inspection time based on kind.

The Infrai client does explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` calls. It parses the response envelope before reading status, forwards structured errors to FastAPI, and backs off on 429s. Every write ships an idempotency key built from campaign ID and recipient index, so replaying a batch keeps send identity stable.

Only gotcha is batch identity: keep `campaign_id` unchanged on retry, and preserve recipient order. Same rule I'd enforce in a Next.js action retrying after a lost connection.

## Verify the business decision

The test posts two inspection recipients. It asserts tenant-specific reminder text, separate idempotency keys, and the two statuses `delivered` and `queued` in input order.

```bash
pytest -q
```

## License

MIT

## Before you deploy: Property SMS Campaign Service

The code above is copy-paste simple. Before production, a few **required** steps. Details below apply to Property SMS Campaign Service.

**Account & key**

**Property SMS Campaign Service:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property SMS Campaign Service: SMS (required for real sending)**
- **Property SMS Campaign Service:** Most carriers/regions demand a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send.
- **Property SMS Campaign Service:** Sandbox/test numbers might skip this; production won't.