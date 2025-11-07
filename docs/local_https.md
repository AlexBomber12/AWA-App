# Local HTTPS

Several browser integrations (Keycloak, OAuth callbacks, embedded widgets) require HTTPS even in development. This guide standardizes how we create trusted certificates with `mkcert`, wire them into docker-compose, and trust them on every OS.

## Generate certificates with mkcert
1. Install mkcert + the NSS tools:
   ```bash
   brew install mkcert nss        # macOS
   choco install mkcert nss-tools # Windows (admin PowerShell)
   sudo apt install mkcert libnss3-tools # Debian/Ubuntu
   ```
2. Create a local CA:
   ```bash
   mkcert -install
   ```
3. Issue a cert for the dev hostnames you need (add wildcards as required):
   ```bash
   mkcert localhost 127.0.0.1 ::1 api.local awa.local
   ```
   The command writes `localhost+4.pem` (cert) and `localhost+4-key.pem` (key) in the current directory. Commit them? **No** — store them under `~/.config/mkcert` or `.local-cert/` and add the directory to `.gitignore`.

## Wire certificates into docker-compose
1. Copy or symlink the cert/key into `infra/certs/` (ignored by Git):
   ```bash
   mkdir -p infra/certs
   cp ~/.local/share/mkcert/localhost+4.pem infra/certs/dev.crt
   cp ~/.local/share/mkcert/localhost+4-key.pem infra/certs/dev.key
   ```
2. Update or extend `docker-compose.dev.yml` with an HTTPS reverse proxy:
   ```yaml
   https-proxy:
     image: caddy
     volumes:
       - ./infra/certs/dev.crt:/etc/certs/dev.crt:ro
       - ./infra/certs/dev.key:/etc/certs/dev.key:ro
     environment:
       - API_UPSTREAM=http://api:8000
     ports:
       - "8443:443"
   ```
3. Point your browser/client to `https://localhost:8443` (or whichever hostname you minted) and confirm the certificate shows as trusted.

## OS trust-store tips
- **macOS:** `mkcert -install` adds the CA to the System keychain. If Safari/Chrome still warn, open Keychain Access → “System” → search for “mkcert” → double-click the CA → set “Always Trust”.
- **Windows:** run PowerShell as Administrator before `mkcert -install`. Certificates land in “Trusted Root Certification Authorities.” If WSL services need trust, copy the `.pem` into `/usr/local/share/ca-certificates` and run `sudo update-ca-certificates`.
- **Linux:** install `ca-certificates` + `mkcert`, then run `sudo update-ca-certificates` after `mkcert -install`. For browsers using their own store (Firefox), open Preferences → Privacy & Security → “View Certificates” → Authorities → Import the mkcert CA.

## Reverse-proxy notes
- Keep HTTPS termination in a dedicated container (Caddy, Traefik, or nginx) so services keep listening on HTTP.
- Mount the generated certs read-only and reload the proxy when you rotate them.
- For Next.js or other frontends, set `NEXT_PUBLIC_API_URL=https://api.local:8443` so the browser fetches through HTTPS.

## See also
- [Testing](TESTING.md)
- [Agents](agents.md)
- [CI Debug](CI_debug.md)
