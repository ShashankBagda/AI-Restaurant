function LandingView() {
  const go = (target) => {
    window.location.hash = `/${target}`;
  };

  return (
    <div className="container landing">
      <div className="page-hero fade-up">
        <div className="card hero">
          <div className="hero-accent" />
          <div className="badge-row">
            <span className="badge">MVP live</span>
            <span className="badge">Local Wi-Fi ready</span>
            <span className="badge">AI recommendations</span>
          </div>
          <h2>Smart Restaurant OS</h2>
          <p className="status">
            A full-stack dining experience that automates entry, ordering, kitchen flow,
            and feedback - while keeping the human touch.
          </p>
          <div className="stat-grid">
            <div className="stat-card">
              <strong>Entry to Exit</strong>
              <span className="status">One connected flow</span>
            </div>
            <div className="stat-card">
              <strong>Live Sync</strong>
              <span className="status">WebSocket orders</span>
            </div>
            <div className="stat-card">
              <strong>Personalized</strong>
              <span className="status">Taste profiles + ratings</span>
            </div>
          </div>
        </div>
        <div className="hero-illust floating">
          <svg viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="16" y="18" width="208" height="144" rx="26" fill="#F3EEE7" stroke="#D9C8B8" strokeWidth="2"/>
            <path d="M48 60H192" stroke="#2D6A75" strokeWidth="3" strokeLinecap="round"/>
            <path d="M48 88H170" stroke="#D46B4A" strokeWidth="3" strokeLinecap="round"/>
            <path d="M48 116H140" stroke="#7A8F5B" strokeWidth="3" strokeLinecap="round"/>
            <circle cx="176" cy="118" r="18" fill="#FCE7DC" stroke="#E3C7B7" strokeWidth="2"/>
            <path d="M170 118L176 124L186 108" stroke="#2D6A75" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>

      <div className="section-title fade-up">
        <h3>Experience Flow</h3>
        <p className="status">A redesigned journey from arrival to feedback.</p>
      </div>
      <div className="flow-grid">
        {[
          ["01", "Entry & seating", "AI assigns the best table based on party size, preference, and occasion."],
          ["02", "Smart menu", "Personalized recommendations with dietary and regional context."],
          ["03", "Kitchen sync", "Orders route to chefs by category and specialty."],
          ["04", "Immersive dining", "Ambience themes and table projection set the mood."],
          ["05", "Robot delivery", "Fast, hygienic food delivery with staff on hospitality."],
          ["06", "Learning loop", "Ratings feed taste profiles and improve future suggestions."]
        ].map(([step, title, desc]) => (
          <div key={step} className="flow-card fade-up">
            <div className="flow-step">{step}</div>
            <h4>{title}</h4>
            <p className="status">{desc}</p>
          </div>
        ))}
      </div>

      <div className="info-grid" style={{ marginTop: 20 }}>
        <div className="card fade-up">
          <h3>Local network topology</h3>
          <p className="status">
            A main server PC orchestrates orders. Customer tablets and kitchen screens
            auto-discover the server over Wi-Fi.
          </p>
          <div className="mini-diagram">
            <div className="node">Server</div>
            <div className="node">Admin</div>
            <div className="node">Customer</div>
            <div className="node">Kitchen</div>
          </div>
        </div>
        <div className="card fade-up">
          <h3>Built for the future</h3>
          <p className="status">
            Multi-language support, AI-driven kitchen optimization, IoT integrations,
            and franchise-ready deployment.
          </p>
          <div className="row" style={{ marginTop: 12 }}>
            <div className="pill">Computer vision</div>
            <div className="pill">Robotics</div>
            <div className="pill">Projection AR</div>
          </div>
        </div>
      </div>

      <div className="section-title fade-up" style={{ marginTop: 24 }}>
        <h3>End-to-end automation map</h3>
        <p className="status">See how every station syncs from entry to feedback.</p>
      </div>
      <div className="diagram-card fade-up">
        <div className="diagram-track">
          <div className="diagram-node">
            <div className="node-icon">01</div>
            <div>
              <strong>Entry + Seating</strong>
              <div className="status">AI assigns table</div>
            </div>
          </div>
          <div className="diagram-node">
            <div className="node-icon">02</div>
            <div>
              <strong>Menu + AI</strong>
              <div className="status">Taste-based picks</div>
            </div>
          </div>
          <div className="diagram-node">
            <div className="node-icon">03</div>
            <div>
              <strong>Kitchen Flow</strong>
              <div className="status">Auto assign by specialty</div>
            </div>
          </div>
          <div className="diagram-node">
            <div className="node-icon">04</div>
            <div>
              <strong>Delivery</strong>
              <div className="status">Robot + staff service</div>
            </div>
          </div>
          <div className="diagram-node">
            <div className="node-icon">05</div>
            <div>
              <strong>Feedback</strong>
              <div className="status">Learns preferences</div>
            </div>
          </div>
        </div>
      </div>

      <div className="section-title fade-up" style={{ marginTop: 24 }}>
        <h3>Table UI preview</h3>
        <p className="status">A quick look at the customer table experience.</p>
      </div>
      <div className="mock-grid">
        <div className="mock-card fade-up">
          <div className="mock-header">
            <div>
              <strong>Table T1</strong>
              <div className="status">Welcome back, Shash</div>
            </div>
            <span className="pill">Live</span>
          </div>
          <div className="mock-menu">
            <div className="mock-item">
              <div className="mock-thumb" />
              <div>
                <strong>Masala Peanut</strong>
                <div className="status">Chakna</div>
              </div>
              <span className="mock-price">$ 300</span>
            </div>
            <div className="mock-item">
              <div className="mock-thumb" />
              <div>
                <strong>Paneer Tikka</strong>
                <div className="status">Starter</div>
              </div>
              <span className="mock-price">$ 420</span>
            </div>
            <div className="mock-item">
              <div className="mock-thumb" />
              <div>
                <strong>Chocolate Lava Cake</strong>
                <div className="status">Dessert</div>
              </div>
              <span className="mock-price">$ 280</span>
            </div>
          </div>
          <div className="mock-cart">
            <div className="mock-cart-row">
              <span>Masala Peanut x1</span>
              <strong>$ 300</strong>
            </div>
            <div className="mock-cart-row">
              <span>Paneer Tikka x1</span>
              <strong>$ 420</strong>
            </div>
            <div className="mock-cart-total">
              <span>Total</span>
              <strong>$ 720</strong>
            </div>
            <div className="mock-payments">
              <span className="pay-chip">Card</span>
              <span className="pay-chip">UPI</span>
              <span className="pay-chip">Cash</span>
            </div>
          </div>
          <div className="mock-actions">
            <button className="btn btn-primary">Add to cart</button>
            <button className="btn btn-secondary">Ask chef</button>
            <button className="btn btn-ghost">Checkout</button>
          </div>
          <div className="chef-overlay">
            <div className="chef-video" />
            <div>
              <strong>Chef Call</strong>
              <div className="status">Custom spice level + allergy notes</div>
            </div>
          </div>
        </div>
        <div className="card fade-up">
          <h3>Immersive ambience</h3>
          <p className="status">
            The system adapts lighting, table projection, and playlist to match the occasion.
          </p>
          <div className="ambience-strip">
            <div className="ambience-dot" />
            <div className="ambience-dot" />
            <div className="ambience-dot" />
          </div>
          <div className="status" style={{ marginTop: 10 }}>
            Example: Anniversary theme, warm lighting, and curated dessert picks.
          </div>
        </div>
      </div>

    </div>
  );
}
