# Production Roadmap

This repo is a Docker Compose build for a coding test, not a deployed
system. If this were going to production, here's what would change:

**Infrastructure.** React build → S3 + CloudFront. FastAPI → ECS Fargate
behind an ALB. Postgres → RDS in a private subnet (encrypted, automated
backups). Secrets → Secrets Manager, not env vars in a compose file. All
provisioned via CloudFormation/Terraform, not run locally by hand.

**Auth.** Replace the demo credential store and self-issued JWT with a
managed OIDC provider (Cognito/Auth0/Okta) using Authorization Code +
PKCE — see the README's "Authentication" section for why.

**Deploy.** Keep GitHub Actions for CI; add a gated deploy job that
builds/tags an image by commit SHA, pushes to ECR, runs Alembic
migrations, updates the ECS service, and rolls back automatically on a
failed health check.

**Data & tests.** Real migrations instead of `create_all`. Duplicate
sibling names return `409`, not an unhandled error. Integration tests
against real Postgres in CI, not just the fast SQLite-backed ones.

**Operations.** Ship logs/metrics to CloudWatch (or run Prometheus/
Grafana as managed services). Wire the existing Prometheus alert rules
to Alertmanager → Slack/PagerDuty instead of just Prometheus's own UI.
Add an uptime check from outside the cluster, so a monitoring-stack
outage doesn't also hide the app outage. Tune alert thresholds against
real traffic instead of the guesses used here.

This is a list of gaps, not a spec — the point is showing awareness of
the distance between "runs in Docker Compose" and "production," not
designing infrastructure nobody asked for.
