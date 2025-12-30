function KitchenView() {
  const [token, setToken] = useState(localStorage.getItem("sr_token_chef") || "");
  const [deviceId, setDeviceId] = useState("kitchen-01");
  const [tableId, setTableId] = useState("KITCHEN");
  const [userId, setUserId] = useState("chef1");
  const [password, setPassword] = useState("chef123");
  const [status, setStatus] = useState("Not logged in");
  const [orders, setOrders] = useState([]);
  const chefPresets = [
    { id: "chef1", password: "chef123" }
  ];

  const headers = useMemo(() => (token ? { "X-Token": token } : {}), [token]);

  useEffect(() => {
    localStorage.setItem("sr_token_chef", token);
  }, [token]);

  useEffect(() => {
    const wsUrl = apiBase.replace("http", "ws") + "/ws/orders";
    const ws = new WebSocket(wsUrl);
    ws.onmessage = () => refreshOrders();
    return () => ws.close();
  }, [token]);

  useEffect(() => {
    if (token) {
      setStatus("Session restored");
      refreshOrders();
    }
  }, [token]);

  const login = async () => {
    setStatus("Logging in...");
    try {
      const data = await fetchJson(`${apiBase}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: deviceId,
          user_id: userId,
          password,
          table_id: tableId,
        }),
      });
      setToken(data.token);
      setStatus(`Chef ready (${data.specialty || "all"})`);
      refreshOrders();
    } catch (err) {
      setStatus(err.message);
    }
  };

  const refreshOrders = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/orders`, { headers });
      setOrders(data.orders || []);
    } catch (err) {
      if (err.message.includes("token")) {
        setToken("");
        setStatus("Session expired");
      } else {
        setStatus(err.message);
      }
    }
  };

  const updateOrder = async (orderId, statusValue) => {
    await fetchJson(`${apiBase}/api/orders/${orderId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({ status: statusValue }),
    });
    refreshOrders();
  };

  return (
    <div className="container">
      <div className="page-hero fade-up">
        <div className="card hero card-ornate">
          <div className="hero-accent" />
          <h2>Kitchen flow</h2>
          <p className="status">
            <span className="glow-dot" />
            Orders auto-sorted by specialty with live status updates.
          </p>
          <div className="stat-grid">
            <div className="stat-card">
              <strong>{orders.length}</strong>
              <span className="status">Queued orders</span>
            </div>
            <div className="stat-card">
              <strong>{chefPresets.length}</strong>
              <span className="status">Chef presets</span>
            </div>
          </div>
        </div>
        <div className="hero-illust floating">
          <svg viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="22" y="26" width="196" height="128" rx="20" fill="#E9F1EE" stroke="#C9D9D1" strokeWidth="2"/>
            <rect x="44" y="50" width="152" height="16" rx="8" fill="#2D6A75"/>
            <rect x="44" y="78" width="120" height="10" rx="5" fill="#D46B4A"/>
            <rect x="44" y="98" width="140" height="10" rx="5" fill="#7A8F5B"/>
            <circle cx="184" cy="112" r="22" fill="#FCE7DC" stroke="#E3C7B7" strokeWidth="2"/>
            <path d="M176 112H192" stroke="#2D6A75" strokeWidth="3" strokeLinecap="round"/>
          </svg>
        </div>
        <FoodDecor className="decor-right subtle" />
      </div>

      <div className="card fade-up card-ornate">
        <h3>Chef Login</h3>
        <div className="row">
          <select value={userId} onChange={(e) => {
            const preset = chefPresets.find((chef) => chef.id === e.target.value);
            setUserId(e.target.value);
            if (preset) setPassword(preset.password);
          }}>
            {chefPresets.map((chef) => (
              <option key={chef.id} value={chef.id}>{chef.id}</option>
            ))}
          </select>
          <input className="input" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} placeholder="Device ID" />
          <input className="input" value={tableId} onChange={(e) => setTableId(e.target.value)} placeholder="Table ID" />
          <input className="input" value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="User ID" />
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button className="btn btn-primary" onClick={login}>Login</button>
        </div>
        <div className="status">{status}</div>
      </div>

      <div className="card fade-up card-ornate">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3>Orders (Filtered)</h3>
          <button className="btn btn-secondary" onClick={refreshOrders}>Refresh</button>
        </div>
        {orders.map((order) => (
          <div key={order.order_id} className="list-item">
            <strong>{order.order_id}</strong> | Table {order.table_id} | {order.status}
            <div className="status">
              {order.items.map((item) => `${item.name} x${item.quantity}`).join(", ")}
            </div>
            <div className="row">
              {["preparing", "ready", "served"].map((statusValue) => (
                <button key={statusValue} className="btn btn-secondary" onClick={() => updateOrder(order.order_id, statusValue)}>
                  {statusValue}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
