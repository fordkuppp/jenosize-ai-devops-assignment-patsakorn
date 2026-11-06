# Security

Approach and threat assumptions for Jenie Helpdesk AI.

## Threat model

TODO — state what you are defending against and, equally, what you are not. A short honest
model beats a long aspirational one. Starting points:

- The service is internet-facing and unauthenticated in this demo; in production it would sit
  behind the platform's existing identity layer.
- The corpus is internal documentation. Retrieval must not become a way to read documents the
  caller should not see — out of scope here because there is a single tenant, which is itself
  worth stating.
- The model backend is a dependency that can be slow, wrong, or absent. None of those should
  become an availability incident for the rest of the platform.

## Secrets

- Nothing sensitive in the repository. `.env` is gitignored; `.env.example` carries
  placeholders only.
- `gitleaks` scans the full commit history on every pull request and fails the build.
- In AWS, configuration lives in Secrets Manager and is injected at task start — TODO: say
  how, and what the rotation story is.

## Supply chain

- Images build from a pinned minimal base, run as a non-root UID, and carry no shell or
  package manager in the final stage.
- `trivy` scans every built image for HIGH and CRITICAL vulnerabilities and **fails the
  build** rather than reporting and continuing.
- Images are tagged by commit SHA, so a running container maps to an exact commit.

## Pipeline credentials

The infrastructure pipeline holds **no cloud credentials**. Terraform is applied against a
local AWS emulator in CI, so the modules are validated on every pull request without a long-
lived access key existing anywhere. The credential that cannot leak is the one that was never
issued.

TODO: describe how a real deploy would authenticate — GitHub OIDC federated into an IAM role
with a trust policy scoped to this repository and branch, no static keys.

## Least privilege

TODO — the task role grants only what the service uses: read its own secret, write its own
log group, connect to its own database. Say what you excluded and why.

## Rate limiting

TODO — where it is enforced and what the limit is. An unauthenticated endpoint that triggers
model inference is a cost-amplification target: one cheap request causes expensive work.
That framing matters more than the specific number.

## Network

TODO — the database is not publicly reachable; security groups allow only the task to reach
it; TLS terminates at the load balancer.

## WAF

TODO — outline only, per the assignment. Which managed rule groups, and what you would add
for a model-backed endpoint specifically (request size caps, per-IP rate rules).
