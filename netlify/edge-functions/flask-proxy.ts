export default async function handler(request: Request): Promise<Response> {
  const unavailable = (status: number) => new Response(
    "The clinic service is currently unavailable. Please try again later.",
    { status, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } },
  );

  const configuredOrigin = Netlify.env.get("FLASK_BACKEND_URL");
  if (!configuredOrigin) return unavailable(503);

  const incoming = new URL(request.url);
  let backend: URL;
  try {
    backend = new URL(configuredOrigin);
    if (backend.protocol !== "https:" || backend.username || backend.password ||
        backend.pathname !== "/" || backend.search || backend.hash ||
        backend.origin === incoming.origin ||
        backend.hostname.endsWith(".netlify.app")) {
      return unavailable(503);
    }
  } catch {
    return unavailable(503);
  }

  // Assign the path directly so a path beginning with // cannot change the host.
  backend.pathname = incoming.pathname;
  backend.search = incoming.search;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("forwarded");
  headers.delete("x-forwarded-for");
  headers.set("x-forwarded-host", incoming.host);
  headers.set("x-forwarded-proto", "https");

  try {
    const upstream = await fetch(new Request(backend, request), {
      headers,
      redirect: "manual",
      signal: AbortSignal.timeout(25000),
    });
    const responseHeaders = new Headers(upstream.headers);
    const location = responseHeaders.get("location");
    if (location) {
      const destination = new URL(location, backend);
      if (destination.origin === backend.origin) {
        destination.protocol = incoming.protocol;
        destination.host = incoming.host;
        responseHeaders.set("location", destination.href);
      }
    }
    // Clinic pages and session responses must not be cached by shared proxies.
    responseHeaders.set("cache-control", "no-store");
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch {
    return unavailable(502);
  }
}

export const config = { path: "/*" };
