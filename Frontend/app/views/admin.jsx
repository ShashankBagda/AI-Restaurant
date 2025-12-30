function AdminView() {
  const [token, setToken] = useState(localStorage.getItem("sr_token_admin") || "");
  const [deviceId, setDeviceId] = useState("admin-console");
  const [tableId, setTableId] = useState("ADMIN");
  const [userId, setUserId] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [status, setStatus] = useState("Not logged in");
  const [clients, setClients] = useState([]);
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [billing, setBilling] = useState([]);
  const [billingTotal, setBillingTotal] = useState(0);
  const [users, setUsers] = useState([]);
  const [menu, setMenu] = useState([]);
  const [tableFilter, setTableFilter] = useState("");
  const [tab, setTab] = useState("overview");

  const headers = useMemo(() => (token ? { "X-Token": token } : {}), [token]);

  useEffect(() => {
    localStorage.setItem("sr_token_admin", token);
  }, [token]);

  useEffect(() => {
    const wsUrl = apiBase.replace("http", "ws") + "/ws/orders";
    const ws = new WebSocket(wsUrl);
    ws.onmessage = () => refreshOrders();
    return () => ws.close();
  }, [token]);

  useEffect(() => {
    if (token) {
      refreshAll();
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
      setStatus(`Welcome ${data.role}`);
      refreshAll();
    } catch (err) {
      setStatus(err.message);
    }
  };

  const refreshClients = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/clients`, { headers });
      setClients(data.online || []);
    } catch (err) {
      setStatus(err.message);
    }
  };

  const removeClient = async (deviceIdValue) => {
    await fetchJson(`${apiBase}/api/clients/${deviceIdValue}`, { method: "DELETE", headers });
    refreshClients();
  };

  const clearClients = async () => {
    await fetchJson(`${apiBase}/api/clients/clear`, { method: "POST", headers });
    refreshClients();
  };

  const refreshOrders = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/orders`, { headers });
      setOrders(data.orders || []);
    } catch (err) {
      setStatus(err.message);
    }
  };

  const updateOrder = async (orderId, statusValue, assignedTo) => {
    await fetchJson(`${apiBase}/api/orders/${orderId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({ status: statusValue, assigned_to: assignedTo }),
    });
    refreshOrders();
  };

  const refreshInventory = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/inventory`, { headers });
      setInventory(data.items || []);
    } catch (err) {
      setStatus(err.message);
    }
  };

  const updateInventory = async (itemId, stock) => {
    await fetchJson(`${apiBase}/api/inventory/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({ stock: parseInt(stock, 10) || 0 }),
    });
    refreshInventory();
  };

  const refreshBilling = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/billing`, { headers });
      setBilling(data.payments || []);
      setBillingTotal(data.total || 0);
    } catch (err) {
      setStatus(err.message);
    }
  };

  const refreshUsers = async () => {
    if (!token) return;
    const data = await fetchJson(`${apiBase}/api/users`, { headers });
    setUsers(data.users || []);
  };

  const refreshMenu = async () => {
    if (!token) return;
    const data = await fetchJson(`${apiBase}/api/menu/admin`, { headers });
    setMenu(data.items || []);
  };

  const refreshAll = () => {
    refreshClients();
    refreshOrders();
    refreshInventory();
    refreshBilling();
    refreshUsers();
    refreshMenu();
  };
  return (
    <div className="container">
      <div className="page-hero fade-up">
        <div className="card hero">
          <div className="hero-accent" />
          <h2>Command center</h2>
          <p className="status">
            <span className="glow-dot" />
            Track systems, orders, inventory, and billing in one view.
          </p>
          <div className="stat-grid">
            <div className="stat-card">
              <strong>{clients.length}</strong>
              <span className="status">Systems online</span>
            </div>
            <div className="stat-card">
              <strong>{orders.length}</strong>
              <span className="status">Active orders</span>
            </div>
            <div className="stat-card">
              <strong>{inventory.length}</strong>
              <span className="status">Inventory items</span>
            </div>
          </div>
        </div>
        <div className="hero-illust floating">
          <svg viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="24" width="200" height="132" rx="20" fill="#F3F1E7" stroke="#DACCBF" strokeWidth="2"/>
            <rect x="40" y="44" width="70" height="10" rx="5" fill="#D46B4A"/>
            <rect x="40" y="64" width="120" height="8" rx="4" fill="#2D6A75"/>
            <rect x="40" y="84" width="140" height="8" rx="4" fill="#7A8F5B"/>
            <rect x="40" y="104" width="90" height="8" rx="4" fill="#D46B4A"/>
            <circle cx="178" cy="94" r="26" fill="#FCE7DC" stroke="#E3C7B7" strokeWidth="2"/>
            <path d="M168 92L178 102L192 84" stroke="#2D6A75" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>

      <div className="card fade-up">
        <h3>Admin Login</h3>
        <div className="row">
          <input className="input" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} placeholder="Device ID" />
          <input className="input" value={tableId} onChange={(e) => setTableId(e.target.value)} placeholder="Table ID" />
          <input className="input" value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="User ID" />
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button className="btn btn-primary" onClick={login}>Login</button>
        </div>
        <div className="status">{status}</div>
      </div>

      <div className="card fade-up" style={{ marginTop: 20 }}>
        <div className="row">
          {["overview", "orders", "inventory", "billing", "users", "menu"].map((item) => (
            <button
              key={item}
              className={`btn ${tab === item ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTab(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      {tab === "overview" && (
        <div className="grid grid-2" style={{ marginTop: 20 }}>
          <div className="card fade-up">
            <h3>Systems Online ({clients.length})</h3>
            <div className="row">
              <button className="btn btn-secondary" onClick={refreshClients}>Refresh</button>
              <button className="btn btn-secondary" onClick={clearClients}>Clear</button>
            </div>
            {clients.map((client) => (
              <div key={client.device_id} className="list-item">
                {client.device_id} ({client.table_id})
                <button className="btn btn-secondary" style={{ marginLeft: 8 }} onClick={() => removeClient(client.device_id)}>
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="card fade-up">
            <h3>Billing</h3>
            <div className="status">Total: $ {billingTotal.toFixed(2)}</div>
            {billing.map((payment) => (
              <div key={payment.payment_id} className="list-item">
                {payment.order_id} | $ {payment.amount.toFixed(2)} | {payment.method}
              </div>
            ))}
            <button className="btn btn-secondary" onClick={refreshBilling}>Refresh</button>
          </div>
        </div>
      )}

      {tab === "orders" && (
        <div className="card fade-up" style={{ marginTop: 20 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>Orders</h3>
            <input className="input input-inline" value={tableFilter} onChange={(e) => setTableFilter(e.target.value)} placeholder="Filter by table" />
          </div>
          {orders
            .filter((order) => !tableFilter || order.table_id.toLowerCase().includes(tableFilter.toLowerCase()))
            .map((order) => (
              <div key={order.order_id} className="list-item">
                <strong>{order.order_id}</strong> | Table {order.table_id} | {order.status} | {order.payment_status}
                <div className="status">
                  {order.items.map((item) => `${item.name} x${item.quantity}${item.assigned_to ? " -> " + item.assigned_to : ""}`).join(", ")}
                </div>
                <div className="row">
                  {["preparing", "ready", "served"].map((statusValue) => (
                    <button
                      key={statusValue}
                      className="btn btn-secondary"
                      onClick={() => updateOrder(order.order_id, statusValue, null)}
                    >
                      {statusValue}
                    </button>
                  ))}
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      const chefId = prompt("Chef user_id");
                      if (chefId) updateOrder(order.order_id, order.status, chefId);
                    }}
                  >
                    assign chef
                  </button>
                </div>
              </div>
            ))}
          <button className="btn btn-secondary" onClick={refreshOrders}>Refresh</button>
        </div>
      )}

      {tab === "inventory" && (
        <div className="grid grid-2" style={{ marginTop: 20 }}>
          <div className="card fade-up">
            <h3>Inventory</h3>
            {inventory.map((item) => (
              <div key={item.item_id} className="list-item">
                {item.name || item.item_id}
                <div className="row">
                  <input className="input input-inline" type="number" defaultValue={item.stock} onBlur={(e) => updateInventory(item.item_id, e.target.value)} />
                </div>
              </div>
            ))}
            <button className="btn btn-secondary" onClick={refreshInventory}>Refresh</button>
          </div>
          <InventoryChart items={inventory} />
        </div>
      )}

      {tab === "billing" && (
        <div className="card fade-up" style={{ marginTop: 20 }}>
          <h3>Billing</h3>
          <div className="status">Total: $ {billingTotal.toFixed(2)}</div>
          {billing.map((payment) => (
            <div key={payment.payment_id} className="list-item">
              {payment.order_id} | $ {payment.amount.toFixed(2)} | {payment.method}
            </div>
          ))}
          <button className="btn btn-secondary" onClick={refreshBilling}>Refresh</button>
        </div>
      )}

      {tab === "users" && (
        <div className="card fade-up" style={{ marginTop: 20 }}>
          <h3>User Management</h3>
          <UserManager users={users} headers={headers} onRefresh={refreshUsers} />
        </div>
      )}

      {tab === "menu" && (
        <div className="card fade-up" style={{ marginTop: 20 }}>
          <h3>Menu Management</h3>
          <MenuManager menu={menu} headers={headers} onRefresh={refreshMenu} />
        </div>
      )}
    </div>
  );
}

function UserManager({ users, headers, onRefresh }) {
  const [newUserId, setNewUserId] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("customer");
  const [newSpecialty, setNewSpecialty] = useState("");

  const [updateUserId, setUpdateUserId] = useState("");
  const [updatePassword, setUpdatePassword] = useState("");
  const [updateRole, setUpdateRole] = useState("");
  const [updateSpecialty, setUpdateSpecialty] = useState("");

  const [deleteUserId, setDeleteUserId] = useState("");

  const createUser = async () => {
    await fetchJson(`${apiBase}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({
        user_id: newUserId,
        password: newPassword,
        role: newRole,
        specialty: newSpecialty || null,
      }),
    });
    onRefresh();
  };

  const updateUser = async () => {
    const payload = {};
    if (updatePassword) payload.password = updatePassword;
    if (updateRole) payload.role = updateRole;
    if (updateSpecialty) payload.specialty = updateSpecialty;
    await fetchJson(`${apiBase}/api/users/${updateUserId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(payload),
    });
    onRefresh();
  };

  const deleteUser = async () => {
    await fetchJson(`${apiBase}/api/users/${deleteUserId}`, {
      method: "DELETE",
      headers,
    });
    onRefresh();
  };

  return (
    <div>
      <div className="row">
        <input className="input" value={newUserId} onChange={(e) => setNewUserId(e.target.value)} placeholder="User ID" />
        <input className="input" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Password" />
        <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
          <option value="customer">customer</option>
          <option value="admin">admin</option>
          <option value="chef">chef</option>
        </select>
        <input className="input" value={newSpecialty} onChange={(e) => setNewSpecialty(e.target.value)} placeholder="Specialty" />
        <button className="btn btn-secondary" onClick={createUser}>Create</button>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <input className="input" value={updateUserId} onChange={(e) => setUpdateUserId(e.target.value)} placeholder="User ID" />
        <input className="input" type="password" value={updatePassword} onChange={(e) => setUpdatePassword(e.target.value)} placeholder="New Password" />
        <select value={updateRole} onChange={(e) => setUpdateRole(e.target.value)}>
          <option value="">(role)</option>
          <option value="customer">customer</option>
          <option value="admin">admin</option>
          <option value="chef">chef</option>
        </select>
        <input className="input" value={updateSpecialty} onChange={(e) => setUpdateSpecialty(e.target.value)} placeholder="Specialty" />
        <button className="btn btn-secondary" onClick={updateUser}>Update</button>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <input className="input" value={deleteUserId} onChange={(e) => setDeleteUserId(e.target.value)} placeholder="User ID" />
        <button className="btn btn-secondary" onClick={deleteUser}>Delete</button>
      </div>

      <div style={{ marginTop: 12 }}>
        {users.map((user) => (
          <div key={user.user_id} className="list-item">
            {user.user_id} ({user.role}) {user.specialty ? `- ${user.specialty}` : ""}
          </div>
        ))}
        <button className="btn btn-secondary" onClick={onRefresh}>Refresh</button>
      </div>
    </div>
  );
}
function MenuManager({ menu, headers, onRefresh }) {
  const [newId, setNewId] = useState("");
  const [newName, setNewName] = useState("");
  const [newPrice, setNewPrice] = useState("");
  const [newTags, setNewTags] = useState("");
  const [newCategory, setNewCategory] = useState("");

  const [updateId, setUpdateId] = useState("");
  const [updateName, setUpdateName] = useState("");
  const [updatePrice, setUpdatePrice] = useState("");
  const [updateTags, setUpdateTags] = useState("");
  const [updateCategory, setUpdateCategory] = useState("");

  const [deleteId, setDeleteId] = useState("");

  const parseTags = (value) => value.split(",").map((part) => part.trim()).filter(Boolean);

  const createItem = async () => {
    await fetchJson(`${apiBase}/api/menu`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({
        item_id: newId,
        name: newName,
        price: parseFloat(newPrice || 0),
        tags: parseTags(newTags),
        category: newCategory,
      }),
    });
    onRefresh();
  };

  const updateItem = async () => {
    const payload = {};
    if (updateName) payload.name = updateName;
    if (updatePrice) payload.price = parseFloat(updatePrice);
    if (updateTags) payload.tags = parseTags(updateTags);
    if (updateCategory) payload.category = updateCategory;
    await fetchJson(`${apiBase}/api/menu/${updateId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(payload),
    });
    onRefresh();
  };

  const deleteItem = async () => {
    await fetchJson(`${apiBase}/api/menu/${deleteId}`, { method: "DELETE", headers });
    onRefresh();
  };

  return (
    <div>
      <div className="row">
        <input className="input" value={newId} onChange={(e) => setNewId(e.target.value)} placeholder="Item ID" />
        <input className="input" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Name" />
        <input className="input" value={newPrice} onChange={(e) => setNewPrice(e.target.value)} placeholder="Price" />
        <input className="input" value={newTags} onChange={(e) => setNewTags(e.target.value)} placeholder="Tags" />
        <input className="input" value={newCategory} onChange={(e) => setNewCategory(e.target.value)} placeholder="Category" />
        <button className="btn btn-secondary" onClick={createItem}>Create</button>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <input className="input" value={updateId} onChange={(e) => setUpdateId(e.target.value)} placeholder="Item ID" />
        <input className="input" value={updateName} onChange={(e) => setUpdateName(e.target.value)} placeholder="Name" />
        <input className="input" value={updatePrice} onChange={(e) => setUpdatePrice(e.target.value)} placeholder="Price" />
        <input className="input" value={updateTags} onChange={(e) => setUpdateTags(e.target.value)} placeholder="Tags" />
        <input className="input" value={updateCategory} onChange={(e) => setUpdateCategory(e.target.value)} placeholder="Category" />
        <button className="btn btn-secondary" onClick={updateItem}>Update</button>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <input className="input" value={deleteId} onChange={(e) => setDeleteId(e.target.value)} placeholder="Item ID" />
        <button className="btn btn-secondary" onClick={deleteItem}>Delete</button>
      </div>
      <div style={{ marginTop: 12 }}>
        {menu.map((item) => (
          <div key={item.id} className="list-item">
            {item.id} | {item.name} | $ {item.price.toFixed(2)} | {item.category} | {item.tags.join(", ")}
          </div>
        ))}
        <button className="btn btn-secondary" onClick={onRefresh}>Refresh</button>
      </div>
    </div>
  );
}

function InventoryChart({ items }) {
  const maxStock = items.reduce((max, item) => Math.max(max, item.stock || 0), 1);
  return (
    <div className="card fade-up">
      <h3>Inventory Chart</h3>
      {items.map((item) => {
        const percent = Math.round(((item.stock || 0) / maxStock) * 100);
        return (
          <div key={item.item_id} className="list-item">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>{item.name || item.item_id}</span>
              <span>{item.stock}</span>
            </div>
            <div style={{ background: "#f3e6dd", borderRadius: 8, overflow: "hidden", marginTop: 6 }}>
              <div style={{ width: `${percent}%`, height: 10, background: "#d46b4a" }}></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
