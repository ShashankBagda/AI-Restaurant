# Smart Restaurant Wiki

This wiki captures the phased build plan for the Smart Restaurant concept, starting with a hackathon MVP and scaling toward an enterprise-grade platform.

## Phase 1: Hackathon MVP

Goal: deliver a working, end-to-end demo that proves the experience flow.

### Scope (Must-Have)

- Entry and table booking
  - Web form for party size and occasion.
  - Auto table assignment (simple rules).
- Intelligent menu and AI recommendations
  - Menu browsing via web.
  - Basic recommender (popular items + dietary filters).
- Order flow
  - Place order and send to kitchen dashboard.
- Feedback loop
  - 1-click rating after dining to improve future suggestions.

### MVP Tech Stack (Lean)

- Frontend: React (Next.js) or Vite + React.
- Backend: Python (FastAPI) or Node.js (Express).
- Database: SQLite for speed, upgrade path to Postgres.
- Recommender: rules + lightweight scoring (no heavy ML).
- Realtime updates: WebSocket (optional).
- Hosting: Render, Vercel, or Railway.

### MVP Deliverables

- Customer web UI (booking, menu, order).
- Kitchen web UI (incoming orders).
- Basic admin panel (tables, menu items).
- Demo data and flow walkthrough.

### MVP Success Criteria

- Guest can book a table in under 30 seconds.
- Menu recommends 3 items based on simple rules.
- Kitchen receives order instantly.
- Feedback recorded and displayed in admin.

## Phase 2: Enterprise Platform

Goal: production-ready, multi-location platform with AI personalization and automation.

### Enterprise Capabilities

- AI personalization with user profiles across locations.
- Multi-language support and regional personalization.
- CV-based entry detection and table occupancy.
- Robotics and IoT integrations for delivery and ambience.
- Observability, security, and compliance.

### Enterprise Tech Stack (Scalable)

- Backend: Node.js (NestJS) or Python (FastAPI).
- API: REST + GraphQL gateway.
- Database: PostgreSQL + Redis.
- Search and personalization: OpenSearch + feature store (Feast).
- ML platform: PyTorch/TensorFlow + MLflow.
- Messaging: Kafka or RabbitMQ.
- IoT: MQTT broker (EMQX or Mosquitto).
- Robotics: ROS 2 for navigation and fleet control.
- Video calls: WebRTC.
- Cloud: AWS/GCP/Azure + Kubernetes.
- Observability: OpenTelemetry + Prometheus + Grafana.

## Roadmap (Step-by-Step)

1. Ship MVP with a full booking-to-order flow.
2. Add user accounts and taste history.
3. Replace rules with ML-based recommendations.
4. Add multi-location support and data sync.
5. Integrate sensors and robotics.
6. Harden security, monitoring, and compliance.

## Notes

Keep the MVP lean. The goal is to demonstrate a complete, believable experience, not full automation.
