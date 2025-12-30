const { useEffect, useMemo, useState } = React;

const apiBase = (() => {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("server");
  const origin = window.location.origin && window.location.origin !== "null"
    ? window.location.origin
    : "http://127.0.0.1:8000";
  return fromQuery || origin;
})();

function useHashRoute(defaultRoute) {
  const getRoute = () => {
    const hash = window.location.hash.replace("#/", "");
    return hash || defaultRoute;
  };
  const [route, setRoute] = useState(getRoute());
  useEffect(() => {
    const handler = () => setRoute(getRoute());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  return route;
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || "Request failed";
    throw new Error(message);
  }
  return data;
}

function Nav({ route }) {
  const go = (target) => {
    window.location.hash = `/${target}`;
  };
  return (
    <div className="nav">
      <button className={`btn ${route === "customer" ? "btn-primary" : "btn-secondary"}`} onClick={() => go("customer")}>
        Customer
      </button>
      <button className={`btn ${route === "admin" ? "btn-primary" : "btn-secondary"}`} onClick={() => go("admin")}>
        Admin
      </button>
      <button className={`btn ${route === "kitchen" ? "btn-primary" : "btn-secondary"}`} onClick={() => go("kitchen")}>
        Kitchen
      </button>
    </div>
  );
}
