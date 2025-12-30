function CustomerView() {
  const [token, setToken] = useState(localStorage.getItem("sr_token_customer") || "");
  const [deviceId, setDeviceId] = useState("table-01");
  const [tableId, setTableId] = useState("T1");
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [loginStatus, setLoginStatus] = useState("Not logged in");
  const [menu, setMenu] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [recs, setRecs] = useState([]);
  const [cart, setCart] = useState({});
  const [checkoutStatus, setCheckoutStatus] = useState("");
  const [orderStatus, setOrderStatus] = useState("No active order");
  const [history, setHistory] = useState([]);
  const [lastOrderId, setLastOrderId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [rating, setRating] = useState("");
  const [ratingComment, setRatingComment] = useState("");
  const [ratingStatus, setRatingStatus] = useState("");
  const [vegOnly, setVegOnly] = useState(false);
  const [favoriteCategory, setFavoriteCategory] = useState("");
  const [ambience, setAmbience] = useState("luxury");

  const headers = useMemo(() => (token ? { "X-Token": token } : {}), [token]);

  useEffect(() => {
    localStorage.setItem("sr_token_customer", token);
  }, [token]);

  useEffect(() => {
    document.body.setAttribute("data-theme", ambience);
    return () => {
      document.body.removeAttribute("data-theme");
    };
  }, [ambience]);

  useEffect(() => {
    if (!token) return;
    loadMenu();
    loadRecommendations();
    loadHistory();
    loadPreferences();
  }, [token]);

  useEffect(() => {
    const wsUrl = apiBase.replace("http", "ws") + "/ws/orders";
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "order_status" && msg.order_id === lastOrderId) {
          setOrderStatus(`Order ${msg.order_id}: ${msg.status}`);
        }
      } catch (err) {
        // ignore
      }
    };
    return () => ws.close();
  }, [lastOrderId]);

  useEffect(() => {
    const timer = setInterval(() => {
      if (!token) return;
      fetch(`${apiBase}/api/client/ping`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId, table_id: tableId }),
      }).catch(() => {});
    }, 10000);
    return () => clearInterval(timer);
  }, [token, deviceId, tableId]);

  const cartTotal = Object.values(cart).reduce(
    (sum, entry) => sum + entry.item.price * entry.qty,
    0
  );

  const categoryOptions = useMemo(() => {
    const categories = Array.from(new Set(menu.map((item) => item.category).filter(Boolean)));
    categories.sort((a, b) => a.localeCompare(b));
    return ["All", ...categories];
  }, [menu]);

  const filteredMenu = useMemo(() => {
    if (selectedCategory === "All") return menu;
    return menu.filter((item) => item.category === selectedCategory);
  }, [menu, selectedCategory]);

  const login = async () => {
    setLoginStatus("Logging in...");
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
      setLoginStatus(`Welcome ${data.role}`);
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const register = async () => {
    setLoginStatus("Registering...");
    try {
      const data = await fetchJson(`${apiBase}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, password, role: "customer" }),
      });
      setLoginStatus(`Registered ${data.user_id}`);
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const loadMenu = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/menu`, { headers });
      setMenu(data.items || []);
      setSelectedCategory("All");
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const loadRecommendations = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/recommendations`, { headers });
      setRecs(data.items || []);
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const addToCart = (item) => {
    setCart((prev) => {
      const next = { ...prev };
      next[item.id] = next[item.id]
        ? { item, qty: next[item.id].qty + 1 }
        : { item, qty: 1 };
      return next;
    });
  };

  const updateQty = (itemId, delta) => {
    setCart((prev) => {
      const next = { ...prev };
      if (!next[itemId]) return next;
      next[itemId] = { ...next[itemId], qty: next[itemId].qty + delta };
      if (next[itemId].qty <= 0) delete next[itemId];
      return next;
    });
  };

  const checkout = async () => {
    if (!token) {
      setCheckoutStatus("Login required");
      return;
    }
    const items = Object.values(cart).map((entry) => ({
      item_id: entry.item.id,
      quantity: entry.qty,
    }));
    if (!items.length) {
      setCheckoutStatus("Cart is empty");
      return;
    }
    setCheckoutStatus("Placing order...");
    try {
      const order = await fetchJson(`${apiBase}/api/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ table_id: tableId, items }),
      });
      setLastOrderId(order.order_id);
      await fetchJson(`${apiBase}/api/orders/${order.order_id}/pay`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ method: paymentMethod }),
      });
      setCheckoutStatus(`Paid. Order ${order.order_id}`);
      setCart({});
      setOrderStatus("Order placed. Awaiting kitchen.");
      loadHistory();
    } catch (err) {
      setCheckoutStatus(err.message);
    }
  };

  const loadHistory = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/orders/mine`, { headers });
      setHistory(data.orders || []);
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const submitRating = async () => {
    if (!token || !lastOrderId) {
      setRatingStatus("No order to rate");
      return;
    }
    if (!rating) {
      setRatingStatus("Select a rating");
      return;
    }
    setRatingStatus("Submitting...");
    try {
      await fetchJson(`${apiBase}/api/orders/${lastOrderId}/rate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ rating: parseInt(rating, 10), comment: ratingComment || null }),
      });
      setRatingStatus("Thanks for your feedback");
      loadHistory();
    } catch (err) {
      setRatingStatus(err.message);
    }
  };

  const loadPreferences = async () => {
    if (!token) return;
    try {
      const data = await fetchJson(`${apiBase}/api/preferences`, { headers });
      setVegOnly(!!data.veg_only);
      setFavoriteCategory(data.favorite_category || "");
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const savePreferences = async () => {
    if (!token) return;
    try {
      await fetchJson(`${apiBase}/api/preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({
          veg_only: vegOnly,
          favorite_category: favoriteCategory || null,
        }),
      });
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const updatePassword = async () => {
    if (!token || !userId) return;
    try {
      await fetchJson(`${apiBase}/api/profile/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ password }),
      });
      setLoginStatus("Password updated");
    } catch (err) {
      setLoginStatus(err.message);
    }
  };

  const deleteAccount = async () => {
    if (!token) return;
    try {
      await fetchJson(`${apiBase}/api/profile`, {
        method: "DELETE",
        headers,
      });
      setToken("");
      setLoginStatus("Account deleted");
    } catch (err) {
      setLoginStatus(err.message);
    }
  };
  return (
    <div className="container">
      <div className="page-hero fade-up">
        <div className="card hero card-ornate">
          <div className="hero-accent" />
          <h2>Table service, upgraded</h2>
          <p className="status">
            <span className="glow-dot" />
            Instant menu sync, smart picks, and seamless checkout.
          </p>
          <div className="stat-grid">
            <div className="stat-card">
              <strong>Live Menu</strong>
              <span className="status">Always fresh pricing</span>
            </div>
            <div className="stat-card">
              <strong>Smart Picks</strong>
              <span className="status">Based on your taste</span>
            </div>
            <div className="stat-card">
              <strong>Fast Checkout</strong>
              <span className="status">Card, UPI, cash</span>
            </div>
          </div>
        </div>
        <div className="hero-illust floating">
          <svg viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="18" y="20" width="204" height="140" rx="24" fill="#FCE7DC" stroke="#E3C7B7" strokeWidth="2"/>
            <circle cx="120" cy="90" r="42" fill="#FFFFFF" stroke="#D9B7A4" strokeWidth="2"/>
            <circle cx="120" cy="90" r="28" fill="#F7C9A8"/>
            <path d="M70 38C92 54 148 54 170 38" stroke="#2D6A75" strokeWidth="3" strokeLinecap="round"/>
            <rect x="40" y="120" width="64" height="12" rx="6" fill="#D46B4A"/>
            <rect x="136" y="120" width="64" height="12" rx="6" fill="#7A8F5B"/>
          </svg>
        </div>
        <FoodDecor className="decor-right" />
      </div>

      <div className="card hero fade-up card-ornate">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div>
            <h2>Fresh, fast, and made for you</h2>
            <div className="status">Server: {apiBase}</div>
          </div>
          <div className="pill">Customer</div>
        </div>
        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div>
            <h3>Login / Register</h3>
            <div className="row">
              <input className="input" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} placeholder="Device ID" />
              <input className="input" value={tableId} onChange={(e) => setTableId(e.target.value)} placeholder="Table ID" />
              <input className="input" value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="User ID" />
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
              <button className="btn btn-primary" onClick={login}>Login</button>
              <button className="btn btn-secondary" onClick={register}>Register</button>
              <button className="btn btn-ghost" onClick={updatePassword}>Update Password</button>
            </div>
            <div className="status">{loginStatus}</div>
          </div>
          <div>
            <h3>Preferences</h3>
            <div className="row">
              <label>
                <input type="checkbox" checked={vegOnly} onChange={(e) => setVegOnly(e.target.checked)} />
                Veg only
              </label>
              <input className="input" value={favoriteCategory} onChange={(e) => setFavoriteCategory(e.target.value)} placeholder="Favorite category" />
              <button className="btn btn-secondary" onClick={savePreferences}>Save</button>
              <button className="btn btn-ghost" onClick={deleteAccount}>Delete Account</button>
            </div>
          </div>
        </div>
        <div className="card-inline card-ornate" style={{ marginTop: 16 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>Immersive ambience</h3>
            <div className="status">Tap a theme to refresh the table mood</div>
          </div>
          {(() => {
            const themeOptions = [
              ["luxury", "Luxury Restaurant", "Polished golds with low, elegant lighting."],
              ["birthday", "Birthdays", "Playful colors with upbeat energy."],
              ["anniversary", "Wedding Anniversaries", "Soft rose tones and mellow jazz."],
              ["graduation", "Graduations", "Confetti highlights with bright celebratory tones."],
              ["retirement", "Retirement Parties", "Warm tones and relaxed classics."],
              ["promotion", "Promotions or New Jobs", "Bold accents with confident energy."],
              ["engagement", "Engagement Celebrations", "Sparkling highlights and soft romance."],
              ["first-date", "First Dates", "Warm blush lighting and subtle ambience."],
              ["proposal", "Marriage Proposals", "Candlelit focus with dramatic accents."],
              ["valentine", "Valentines Day", "Deep rose palette and soft glow."],
              ["date-night", "Date Night", "Intimate tones with cozy ambiance."],
              ["reunion", "Reuniting After Long Distance", "Warm welcome hues and comfort."],
              ["business-deal", "Closing a Business Deal", "Clean, calm, and focused."],
              ["client-networking", "Client Networking", "Polished neutrals with light sparkle."],
              ["office-holiday", "Office Holiday Parties", "Festive lights and cheerful colors."],
              ["team-lunch", "Team Building Lunches", "Bright, collaborative atmosphere."],
              ["farewell", "Farewell Dinners", "Warm farewell tones and mellow music."],
              ["mothers-day", "Mothers Day", "Floral pastels with gentle warmth."],
              ["fathers-day", "Fathers Day", "Rich walnut and amber tones."],
              ["new-year", "New Years Eve", "Midnight sparkle and bold highlights."],
              ["christmas", "Christmas or Thanksgiving", "Evergreen warmth and candle glow."],
              ["easter", "Easter Brunch", "Soft spring pastels and daylight feel."],
              ["lunar-new-year", "Lunar New Year", "Crimson and gold celebration."],
              ["family-reunion", "Family Reunions", "Comfort tones and shared plates vibe."],
              ["new-home", "Moving into a New Home", "Warm welcome neutrals."],
              ["exam", "Passing a Major Exam", "Bright, uplifting energy."],
              ["sports-win", "Winning a Sports Game", "Bold team colors and excitement."],
              ["goodbye", "Saying Goodbye Before a Long Trip", "Soft farewell tones."],
            ];
            const activeLabel =
              themeOptions.find(([value]) => value === ambience)?.[1] || "Luxury Restaurant";
            return (
              <>
                <div className="theme-grid">
                  {themeOptions.map(([value, label, story]) => (
              <button
                key={value}
                className={`theme-card ${ambience === value ? "active" : ""}`}
                onClick={() => setAmbience(value)}
              >
                <span className={`theme-dot theme-${value}`} />
                <div>
                  <strong>{label}</strong>
                  <div className="theme-story">{story}</div>
                </div>
              </button>
                  ))}
                </div>
                <div className="theme-preview">
                  <div className={`theme-dot theme-${ambience}`} />
                  <div>
                    <strong>Active theme:</strong> {activeLabel}
                  </div>
                </div>
              </>
            );
          })()}
        </div>
        <FoodDecor className="decor-left subtle" />
      </div>

      <div className="grid grid-2" style={{ marginTop: 20 }}>
        <div className="card fade-up card-ornate">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>Menu</h3>
            <button className="btn btn-secondary" onClick={loadMenu}>Refresh</button>
          </div>
          <div className="category-bar">
            {categoryOptions.map((category) => (
              <button
                key={category}
                className={`chip ${selectedCategory === category ? "active" : ""}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>
          <div className="menu-scroll">
            <div className="menu-grid">
              {filteredMenu.map((item) => (
                <div key={item.id} className="menu-card">
                  <h4>{item.name}</h4>
                  <div>{item.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
                  <div className="status">{item.category}</div>
                  <div className="status">$ {item.price.toFixed(2)}</div>
                  <button className="btn btn-primary" onClick={() => addToCart(item)}>Add to cart</button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card fade-up card-ornate">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>AI Recommendations</h3>
            <button className="btn btn-secondary" onClick={loadRecommendations}>Refresh</button>
          </div>
          <div className="menu-grid">
            {recs.map((item) => (
              <div key={item.id} className="menu-card">
                <h4>{item.name}</h4>
                <div>{item.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
                <div className="status">{item.category}</div>
                <div className="status">$ {item.price.toFixed(2)}</div>
                <button className="btn btn-primary" onClick={() => addToCart(item)}>Add to cart</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginTop: 20 }}>
        <div className="card fade-up card-ornate">
          <h3>Cart</h3>
          {Object.values(cart).map((entry) => (
            <div key={entry.item.id} className="cart-item">
              <span>{entry.item.name} x{entry.qty}</span>
              <strong>$ {(entry.item.price * entry.qty).toFixed(2)}</strong>
              <div className="cart-controls">
                <button className="btn btn-secondary" onClick={() => updateQty(entry.item.id, -1)}>-</button>
                <button className="btn btn-secondary" onClick={() => updateQty(entry.item.id, 1)}>+</button>
              </div>
            </div>
          ))}
          <div className="cart-item">
            <strong>Total</strong>
            <span>$ {cartTotal.toFixed(2)}</span>
          </div>
          <div className="row">
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
              <option value="card">Card</option>
              <option value="cash">Cash</option>
              <option value="upi">UPI</option>
            </select>
            <button className="btn btn-primary" onClick={checkout}>Checkout</button>
          </div>
          <div className="status">{checkoutStatus}</div>
        </div>

        <div className="card fade-up card-ornate">
          <h3>Order Status</h3>
          <div className="status">{orderStatus}</div>
          <div style={{ marginTop: 12 }}>
            <h4>Rate your order</h4>
            <div className="row">
              <select className="input-inline" value={rating} onChange={(e) => setRating(e.target.value)}>
                <option value="">Select</option>
                <option value="1">1 star</option>
                <option value="2">2 stars</option>
                <option value="3">3 stars</option>
                <option value="4">4 stars</option>
                <option value="5">5 stars</option>
              </select>
              <input className="input" value={ratingComment} onChange={(e) => setRatingComment(e.target.value)} placeholder="Comment" />
              <button className="btn btn-secondary" onClick={submitRating}>Submit</button>
            </div>
            <div className="status">{ratingStatus}</div>
          </div>
          <div style={{ marginTop: 16 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h4>Order history</h4>
              <button className="btn btn-secondary" onClick={loadHistory}>Refresh</button>
            </div>
            {history.map((order) => (
              <div key={order.order_id} className="list-item">
                {order.order_id} | {order.status} | {order.payment_status} | $ {order.total.toFixed(2)}
                {order.rating ? ` | Rating ${order.rating}` : ""}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
