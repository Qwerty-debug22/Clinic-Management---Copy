The application runs on a separate Python web service. Netlify publishes only
`site/` and forwards requests to that service through an Edge Function. No build
command is required. The Python source, SQLite files, and backup archives are
not published as static assets.

After deploying Flask on your Python host, set `FLASK_BACKEND_URL` in Netlify's
environment variables with Functions runtime scope, then redeploy Netlify.
Use the service's HTTPS origin, without a path, query string, or credentials.
The backend must be a separate Python host, not this Netlify site or another
Netlify proxy. Until it is configured, requests return HTTP 503. Connection
failures return HTTP 502.

Use a production WSGI server on the Python host, with debugging disabled. This
repository contains multiple application copies; select the intended Flask
entry point on that host. Initialize its database and configure production
secrets there. This Netlify change does not deploy or initialize the Python
service, modify its storage, or migrate existing data.

Leave Flask's session cookie Domain unset so cookies belong to the public
Netlify hostname. Enable Secure and HttpOnly session cookies. The proxy forwards
request bodies and cookies, preserves response cookies, rewrites redirects to
the backend origin to use the public hostname, and disables shared caching.
Verify login, logout, redirects, and appointment submissions through Netlify
after connecting the Python service.
