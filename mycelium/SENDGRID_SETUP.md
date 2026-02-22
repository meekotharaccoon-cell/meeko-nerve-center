# SendGrid Setup — Free Tier Alternative (100 emails/day)

If Mailgun's sandbox limitations are an issue, SendGrid is the other free option.

## Setup (5 minutes)

1. sendgrid.com → Sign Up (free, no credit card)
2. Settings → API Keys → Create API Key → Full Access
3. Copy key
4. Add to GitHub Secrets: `SENDGRID_API_KEY`
5. Also add `MAIL_FROM` = your verified sender email
6. Verify your sender email in SendGrid (they send a verification link)

mailer_pro.py detects SendGrid if Mailgun isn't present and uses it automatically.

## SendGrid vs Mailgun Free Tier

| | Mailgun | SendGrid |
|---|---|---|
| Daily limit | 100 | 100 |
| Open tracking | Yes | Yes |
| Dedicated IP | No (free) | No (free) |
| Sandbox restriction | Yes | No |
| Custom domain | Yes | Yes |
| UI | Better logs | Better templates |

Either works. Both beat Gmail App Password for deliverability and tracking.
