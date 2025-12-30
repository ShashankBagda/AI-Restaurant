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

- Frontend: React for table UI and staff dashboard.
- Backend: Python (FastAPI) for REST + WebSocket.
- AI: Python services (same app or separate service).
- Data: SQLite for MVP, upgrade to PostgreSQL later.

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

- Frontend: React for table UI and staff dashboard.
- Backend: Python (FastAPI) for APIs + WebSocket server.
- AI: Python services (same stack or separate service).
- Optional later: Java service only if high-throughput integrations require it.

## Roadmap (Step-by-Step)

1. Ship MVP with a full booking-to-order flow.
2. Add user accounts and taste history.
3. Replace rules with ML-based recommendations.
4. Add multi-location support and data sync.
5. Integrate sensors and robotics.
6. Harden security, monitoring, and compliance.

## Local Network Architecture (Recommended)

For a local Wi-Fi setup where table devices connect to a main server PC, keep the stack simple and Python-first.

### Why Python-First

- AI services are already in Python, so no cross-language friction.
- FastAPI provides strong WebSocket support for real-time table events.
- Faster hackathon iteration with one backend stack.

### Recommended Stack

- Frontend: React for table UI and staff dashboard.
- Backend: Python (FastAPI) for REST + WebSocket.
- AI: Python services (same app or separate microservice).
- Data: SQLite for MVP, upgrade to PostgreSQL later.

### Detailed Diagrams (SVG)

- Architecture overview: `documentation/architecture-overview.svg`
- Detailed sequence: `documentation/sequence-detailed.svg`
- Deployment topology: `documentation/deployment-topology.svg`

### When to Add Java

Only add Java later if you need enterprise-specific integrations or heavy throughput where a JVM service adds clear value. For the MVP, Python keeps everything unified and faster to build.

## Notes

Keep the MVP lean. The goal is to demonstrate a complete, believable experience, not full automation.

## Current Build (Implemented)

- React PWA served by FastAPI at `/app` with routes for landing, customer, admin, and kitchen.
- Customer flow: login/register, menu, cart, checkout, order history, ratings, and AI recommendations.
- Kitchen flow: chef login with specialty filtering, status updates.
- Admin ERP: systems online, orders, billing, inventory, users, and menu management.
- Auth: hashed passwords (PBKDF2) and expiring tokens.
 - Frontend split into files: `Frontend/app/views/landing.jsx`, `Frontend/app/views/customer.jsx`, `Frontend/app/views/admin.jsx`, `Frontend/app/views/kitchen.jsx`, `Frontend/app/shared/shared.jsx`, `Frontend/app/app.jsx`.
