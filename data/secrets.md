# Secrets

Three mechanisms, chosen by who can generate the value.

## Generated in cluster by the operator that owns it

Database credentials. CloudNativePG creates and rotates them and publishes
`jenie-pg-app`. Nothing else should define them — two sources of truth for
one password is how they drift apart.

## Seeded by Terraform

The things Flux cannot source from git because they are needed before Flux
can read anything: the SOPS age key used to decrypt everything else, and the
deploy key image automation commits with. Terraform writes them into
`flux-system` during the platform stage.

Terraform state therefore contains both private keys in plaintext. The state
file is as sensitive as the keys and must be treated that way — it is
gitignored here, and in production belongs in an encrypted remote backend.

## Encrypted in git with SOPS

The object store credential. It has to be in git because SeaweedFS and
CloudNativePG must agree on one value, so neither can generate it.
`.sops.yaml` holds only the age public key and is committed; the private half
lives in `.secrets/` and in the cluster.

Flux decrypts it with the `sops-age` secret via `decryption.provider: sops`
on the apps Kustomization.

## A trap worth knowing

`$(shell cat keyfile)` in a Makefile collapses newlines into spaces. A
multi-line age private key arrives flattened, Terraform stores exactly what
it was given, and SOPS fails with "failed to load age identities" — an error
that names the recipient and the paths it searched, and points at everything
except the build tool. Use `$(file < keyfile)`.

## Not here

Nothing is committed in plaintext. `gitleaks` scans the full history on every
pull request, not just the diff — a secret removed in a later commit is still
a leaked secret.
