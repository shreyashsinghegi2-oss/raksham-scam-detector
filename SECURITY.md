# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting (Security tab, "Report a vulnerability") on this repository.

Include what you found, how to reproduce it, and the impact you expect. I aim to reply within 7 days.

## Scope notes

- The API in `src/raksham/api.py` scores messages in memory and does not store or log message bodies. Messages can contain personal data, so serve it behind HTTPS.
- Set `RAKSHAM_API_KEY` to require an `x-api-key` header. Without it the endpoint is open and should only run on a private network.
- Model output is a statistical guess, not proof. Do not use it as the only basis for blocking a person or an account.
