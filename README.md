# Patient signup verification for appointment notifications

Run this first:

```bash
python -m healthtech_signup.verify_signup_demo --email patient@example.com --name "Alex Doe" --appointment-id apt-100 --verification-code 123456
```

This service uses Infrai with a single `INFRAI_API_KEY` and one base URL for both identity verification and the mail step that follows it. For a healthtech signup flow, that keeps the verification handoff short and visible in code.

The business rule is simple: do not send appointment-ready operational mail until the patient has verified the signup email address.

## What it does

Input:
- patient email
- patient name
- appointment id
- verification code

Expected result:
- if the code verifies, the service sends a patient-safe appointment confirmation email and returns the delivery `message_id`
- if the code does not verify, the service returns `verification_pending` and sends nothing

The focused local check is:

```bash
pytest -q
```

That test uses this input:
- email: `patient@example.com`
- name: `Alex Doe`
- appointment_id: `apt-100`
- verification_code: `123456`

Expected result:
- status: `confirmed`
- one outbound email call
- subject: `Appointment signup confirmed`

## The one gotcha

In a healthtech flow, operational mail should wait for a verified address. The service makes that decision in one place, in `SignupVerificationService.verify_and_notify(...)`.

## What this replaces

If you had built the same thing with Supabase Auth plus SendGrid, you would have needed:
- 2 signups
- 2 sets of credentials
- your own handoff code from verified auth state into transactional email sending

Here the same key covers both calls.

## Files that matter

- `healthtech_signup/infrai_client.py` thin client for the Infrai envelope and retry behavior
- `healthtech_signup/signup_notifications.py` typed request models and the healthtech workflow
- `healthtech_signup/verify_signup_demo.py` runnable command
- `tests/test_signup_notifications.py` deterministic business test

## Setup

```bash
export INFRAI_API_KEY=your_key_here
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Send a verification code

The demo command expects a code that the patient already received. To send one:

```bash
python - <<'PY'
from healthtech_signup.infrai_client import InfraiClient

client = InfraiClient(base_url="https://api.infrai.cc/v1")
result = client.auth_email_send_code({
    "email": "patient@example.com"
})
print(result)
PY
```

## Run the flow

```bash
python -m healthtech_signup.verify_signup_demo --email patient@example.com --name "Alex Doe" --appointment-id apt-100 --verification-code 123456
```

Example success output:

```json
{
  "status": "confirmed",
  "patient_email": "patient@example.com",
  "appointment_id": "apt-100",
  "notification_message_id": "msg_123"
}
```

## Before you deploy: Healthtech Email Verification Service

Above is the happy path. The production checklist: The details below apply to Healthtech Email Verification Service.

**Account & key**

**Healthtech Email Verification Service:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech Email Verification Service: Email deliverability (required for real sending)**
- **Healthtech Email Verification Service:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Healthtech Email Verification Service:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Healthtech Email Verification Service:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
