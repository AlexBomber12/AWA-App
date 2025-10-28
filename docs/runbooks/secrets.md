# Secrets Hardening Runbook

## Why SOPS and age

We store secrets in Git only when they are encrypted with [SOPS](https://github.com/getsops/sops) using age recipients. Encrypted artifacts (`*.enc.yaml`, `*.enc.json`, `*.enc.env`) live under `ops/secrets/`. Plaintext secrets are never committed; `.gitignore` and pre-commit hooks enforce this policy.

This setup protects the repository against accidental secret leaks, keeps developer workflows reproducible, and allows rotations without rewriting history.

## Threat model and commit policy

- **Commit:** Only encrypted secrets with the `.enc.*` suffix go into Git.
- **Never commit:** Private keys, decrypted `.env` files, or raw `secrets.yaml/json/env` files.
- **Review:** Pre-commit runs gitleaks and a plaintext secret guard; CI includes a dedicated gitleaks scan that fails the build on leaks.

## Generate an age key

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
age-keygen -y ~/.config/sops/age/keys.txt   # Copy the Recipient -> .sops.yaml
```

Set the exported recipient in `.sops.yaml` on your local branch before encrypting anything. Never commit the private key (`keys.txt`).

## Encrypting and decrypting with Make

Helper targets wrap `sops` for common tasks:

```bash
# Print the age recipient for the configured private key
make secrets.print-age-recipient

# Encrypt a plaintext secret file
make secrets.encrypt SRC=ops/secrets/dev.yaml DST=ops/secrets/dev.enc.yaml

# Decrypt for local use (never commit the output)
make secrets.decrypt SRC=ops/secrets/dev.enc.yaml DST=.env.local
```

`SRC` must point to a plaintext file outside version control; `DST` should end in `.enc.*` for encrypted files or a local `.env.*` file that remains untracked.

## CI expectations

CI does **not** decrypt secrets. The new `secrets_scan` job runs gitleaks with `.gitleaks.toml` to ensure no plaintext secrets slip through. All other jobs continue unchanged.

## Rotation and incident response

1. Generate a new age key pair as above.
2. Update `.sops.yaml` with the new recipient.
3. Re-encrypt the affected files (`make secrets.encrypt ...`).
4. Validate with pre-commit and CI; open a PR documenting the rotation.

In an incident, revoke the leaked credentials, rotate keys, and re-encrypt the impacted files. Never add private keys or decrypted secrets to the repository history.
