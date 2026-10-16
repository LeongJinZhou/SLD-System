# Connect QIU Google sign-in

This setup needs a QIU Google Cloud project owner. The application is ready to start OAuth, but no client credentials are configured on this machine. Do not paste a client secret into chat or enter it into the website.

## 1. Create the university OAuth client

1. Sign in to [Google Cloud Console](https://console.cloud.google.com/) with the QIU account that manages the project. Create or select a university-owned project, such as **QIU SLD Prototype**.
2. Open **Google Auth Platform → Branding**. Enter the application name **QIU Student Life Division**, a support email and developer contact.
3. Under **Audience**, select **Internal** when the project belongs to QIU's Workspace organization. If Internal is unavailable, ask QIU IT to establish the university project. For an authorized external testing project, add the intended QIU accounts as test users.
4. Under **Clients**, create a **Web application** client named **SLD Local Prototype**.
5. Set **Authorized JavaScript origins** to `http://127.0.0.1:8765`.
6. Set **Authorized redirect URIs** to `http://127.0.0.1:8765/auth/callback` and save. Use this exact address; `localhost` is a different host.
7. Download the client JSON file and keep it outside the project, for example in a private local credentials folder. The launcher reads its `web.client_id` and `web.client_secret`. Do not commit or share this file.

Client creation and exact redirect matching follow [Google's OpenID Connect setup](https://developers.google.com/identity/openid-connect/openid-connect). Audience and branding are documented in [Google's consent-screen guide](https://developers.google.com/workspace/guides/configure-oauth-consent).

## 2. Start the configured local prototype

Close the existing prototype server through its terminal first. In PowerShell, from this project directory:

```powershell
.\tools\start_google.ps1 -ClientJson 'C:\private\qiu-sld-client.json' -AdminEmails 'your.sld.account@qiu.edu.my'
```

Replace the two values with your private JSON path and actual SLD account. Multiple admins use a comma-separated list. The launcher validates the local callback and QIU admin emails, loads credentials into the server process, and restores the calling process environment after exit. It never prints or saves the secret. It uses the bundled Python runtime when available, otherwise `python` on PATH.

Open `http://127.0.0.1:8765/`. Google sign-in appears above seven fictional test roles. This mixed **local prototype** uses `data/preview.sqlite3`; verified Google identity does not make the database an official university service. Do not use real student records or financial evidence in this test database. Add `-OfficialMode` only when intentionally running the separate `data/sld.sqlite3` database with test buttons disabled. Hosting and operational readiness remain separate prerequisites.

## 3. Enable directory information

In the same project, enable **People API**. Add `https://www.googleapis.com/auth/directory.readonly` to the app's requested access under **Data Access**, and ask QIU IT to permit this application and the directory/profile sharing required by university policy. Restart with:

```powershell
.\tools\start_google.ps1 -ClientJson 'C:\private\qiu-sld-client.json' -AdminEmails 'your.sld.account@qiu.edu.my' -Directory
```

Sign in again to grant the additional scope. In the mixed prototype, directory searches/imports intentionally remain fictional fixtures even for a Google-authenticated account; login can capture its own available profile. To verify the real university contact directory, stop that server and run the separate mode with **both** switches:

```powershell
.\tools\start_google.ps1 -ClientJson 'C:\private\qiu-sld-client.json' -AdminEmails 'your.sld.account@qiu.edu.my' -Directory -OfficialMode
```

This selects `data/sld.sqlite3` and disables all fictional test-role buttons. It remains a local setup/verification server, not a deployed production service. QIU's directory settings determine which people and fields are returned; [Google's directory documentation](https://developers.google.com/people/v1/directory) describes that access. The system imports only available names, email, photos, organizations and external IDs. Missing programme, student ID or person type needs an authorized university mapping; the system does not invent them. SLD staff use department, not programme. Directory titles never grant SLD privileges.

## 4. Check the connection

- A QIU account signs in and shows **Google verified identity**. A personal Gmail account is rejected.
- The allowlisted SLD account receives SLD access; another university account does not automatically become an administrator.
- With Directory and OfficialMode enabled, search for a known student. Inspect name, photo, full ID and programme. SLD can import the visible directory through Contacts. Mixed prototype directory searches/imports use fictional fixtures.
- Test roles remain clearly fictional and available only in prototype mode. They are separate users from the real QIU account.

No real Google login or full university directory import has been verified in this workspace yet. These checks require your configured QIU client.

## Troubleshooting

| Message | Action |
|---|---|
| Google setup required | Start using the launcher; restarting the unconfigured preview does not load credentials. |
| redirect_uri_mismatch | Match the exact callback above and open 127.0.0.1, not localhost. |
| Access blocked / admin approval required | QIU IT must allow the app/scopes or correct its Audience/test users. |
| Invalid client | Check the JSON belongs to a Web application client and its secret remains valid. |
| Directory unavailable | Confirm People API, requested scope and QIU sharing/app-access policy, then sign in again. |
| Port already in use | Close the existing server terminal. Do not start two servers on port 8765. |
| Session expired after restart | Sign in again. Browser-held draft recovery is limited to the same account. |

For future hosting, register the exact university-approved HTTPS callback and set `SLD_APP_URL` to its public origin. The local launcher intentionally supports only this localhost prototype; do not reuse its test mode as deployment configuration.
