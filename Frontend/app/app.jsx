function App() {
  const route = useHashRoute("landing");
  const isLanding = route === "landing";
  return (
    <>
      <header>
        <div className="brand">Smart Restaurant</div>
        {isLanding ? (
          <div className="nav">
            <button className="btn btn-primary" onClick={() => (window.location.hash = "/customer")}>
              Customer
            </button>
            <button className="btn btn-secondary" onClick={() => (window.location.hash = "/admin")}>
              Admin
            </button>
            <button className="btn btn-ghost" onClick={() => (window.location.hash = "/kitchen")}>
              Kitchen
            </button>
          </div>
        ) : (
          <Nav route={route} />
        )}
      </header>
      {isLanding && <LandingView />}
      {route === "customer" && <CustomerView />}
      {route === "admin" && <AdminView />}
      {route === "kitchen" && <KitchenView />}
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
