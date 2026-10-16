# Host QIU Student Life Division on Exabytes

Updated 2026-10-08. The application uses Python with a MySQL-compatible InnoDB database in production. The existing SQLite database remains a local preview/migration source. This guide prepares deployment; no connection to QIU's Exabytes account has been made.

## Hosting target and evidence

Exabytes Malaysia's current [cPanel specification](https://www.exabytes.my/web-hosting/cpanel-web-hosting/features) advertises Python 3.12.x and MariaDB 10.11.x. MariaDB speaks the MySQL protocol used by this application; it is a separate database product, not proof of an Oracle MySQL installation. QIU's purchased server may differ. [cPanel Application Manager](https://docs.cpanel.net/cpanel/software/application-manager/) requires provider-enabled Passenger support. Python appearing in a feature list does not establish that the purchased account can run a Python web application.

Use a dedicated domain/subdomain, for example `https://sld.qiu.edu.my`, mounted at `/`. The application uses root-relative API/assets and does not support a `/sld` subdirectory deployment. Required capabilities:

| Capability | Why it is needed |
|---|---|
| Python 3.12+ with a virtual environment and pip | Existing backend and dependencies |
| Passenger/WSGI on cPanel, or a WSGI server on a VPS | Runs `application` from `passenger_wsgi.py` or `wsgi.py`; does not expose the localhost development server |
| MySQL-compatible InnoDB, utf8mb4, transactions and GET_LOCK | Unicode data, shared-worker mutation serialization and atomic approval posting |
| Private writable application/data directory | Server files and operational data must be outside public_html |
| HTTPS and outbound access to approved Google endpoints | Secure university OAuth and directory requests |
| LibreOffice Writer/soffice plus Unicode fonts | Converts the retained proposal DOCX into the same-format PDF |
| Sufficient connection/process/memory limits | Each application worker has a database connection; PDF conversion also needs memory/process allowance |

Original-template PDF is a material hosting requirement. If the shared account cannot execute LibreOffice, ask QIU IT/Exabytes to provide an approved renderer or run this application on the existing Exabytes VPS/server with that capability. Word export alone does not satisfy the required PDF workflow. Generated club/finance reports use ReportLab and have a portable Chinese-font fallback; exact display still needs PDF acceptance on the target server.

## Server configuration

Set environment variables through the hosting panel or a private owner-readable environment file. Never put secrets in web files, Git, chat, screenshots or shell command arguments.

| Variable | Value/purpose |
|---|---|
| SLD_ENV | `production` |
| SLD_STORAGE | `mysql` |
| SLD_APP_URL | Public HTTPS origin with no path, query or trailing application directory |
| MYSQL_HOST | Host supplied by Exabytes, often `localhost` |
| MYSQL_PORT | Supplied port, default `3306` |
| MYSQL_DATABASE | Full cPanel-prefixed university database name |
| MYSQL_USER / MYSQL_PASSWORD | Dedicated application account; keep privileges limited to its database |
| MYSQL_SSL_CA | Trusted CA file when the database connection requires TLS |
| SLD_SESSION_ENCRYPTION_KEY | Stable private Fernet key; same key for every worker, protected with backups |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | University-owned OAuth web client |
| SLD_ADMIN_EMAILS | Comma-separated authorized QIU SLD email allowlist |
| GOOGLE_DIRECTORY_ENABLED | `true` only after university-approved API/directory permissions are ready |
| SLD_DATA_DIR | Private owner-writable data directory outside public_html |
| SOFFICE_PATH | Actual permitted Linux `soffice` path, if it is not on PATH |

Generate the encryption key locally with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, then store it privately. Keep it stable across restarts. Changing it invalidates encrypted sessions. The opaque cookie never contains the OAuth token; encrypted server sessions expire and sign-out revokes them across workers.

## cPanel / Passenger

1. QIU IT verifies **Setup Python App** or **Application Manager** is enabled for the existing account, chooses Python 3.12+, and configures the dedicated HTTPS domain/subdomain.
2. Upload the application outside `public_html`, including `web/`, `tokens.css`, `templates/event-proposal.docx`, Python modules and requirements. Do not upload preview databases, `.agency/`, `.tools/`, private credentials or test artifacts into a public document root. Provision the Linux renderer separately; the local Windows executable cannot run on Linux.
3. Configure application root, URI `/`, startup file `passenger_wsgi.py`, and entry point `application`. Select the virtual environment using the panel-provided command. Run `python -m pip install -r requirements.txt` in that environment.
4. Create the MySQL/MariaDB database and dedicated database user in the panel. Apply `mysql_schema.sql` with the operator's schema privilege before switching traffic. Use the migration tool only when importing an approved existing dataset; fictional preview data must not be imported into the official service.
5. Set the environment values above, including production mode, HTTPS origin and stable encryption key. Register `https://<actual-domain>/auth/callback` in the university Google OAuth client. Update Google allowed origin to the exact application origin.
6. Run `python tools/hosting_check.py --connect`. It performs configuration/dependency checks and read-only database/version/schema checks without printing secrets. A pass does not prove the provider enabled Passenger, actual Google permissions, backups, PDF rendering or load capacity.
7. Restart with the panel control. For Passenger, the [official cPanel WSGI instructions](https://docs.cpanel.net/knowledge-base/web-services/how-to-install-a-python-wsgi-application/) describe touching the application's `tmp/restart.txt` file after changes.
8. Complete the acceptance checks below on a staging domain before official use. Do not use `server.py --preview` or expose port 8765 as the official service.

## Exabytes VPS / dedicated server

The same `wsgi:application` callable can run under a university-managed WSGI server such as Gunicorn behind an HTTPS reverse proxy. Install the Python requirements in a virtual environment and the approved Linux LibreOffice/fonts through server operations. Bind the WSGI process to loopback or a Unix socket; proxy the dedicated domain root to it. Supply the same environment variables, schema and private data permissions. Manage the process with the server's service manager and ensure worker/database limits fit the purchased server. No reverse-proxy, server package or service configuration has been applied by this local task.

## Migration, backup and acceptance

Keep a consistent backup of the source SQLite database. The explicit migration tool checks source/target state and imports records/audit data into the separate MySQL target; review its actual help before executing. Source files must remain unchanged. Exclude preview accounts/data from official migration. Back up MySQL through the hosting panel or a university-managed transaction-consistent database backup; `tools/backup.py` is for SQLite and cannot back up MySQL. Also retain the private session encryption key and configuration in the approved secret backup system.

Staging acceptance must verify live university sign-in, club and event access, advisor/SLD review, returned corrections, notifications/read state and revoked-recipient isolation; multilingual original-format Word/PDF/Excel exports; receipt downloads; concurrent approval/revision rejection; automatic calendar entries; backup restore and measured workload. Test desktop/mobile scrolling, keyboard focus and long forms. Verify that preview login is absent and that database/private application files cannot be served directly.

Current evidence and open release requirements are recorded in [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md). Hosting configuration remains incomplete until the actual Exabytes account capabilities and credentials are checked privately.
