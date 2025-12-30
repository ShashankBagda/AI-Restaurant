# Smart Restaurant

End-to-End Hospitality Automation Using AI and Software

Smart Restaurant is a next-generation restaurant automation concept that transforms the entire dining experience using Artificial Intelligence, software systems, and smart hardware.

The goal is simple: reduce repetitive human tasks, improve efficiency, and deliver a highly personalized dining experience across locations.

## Why This Exists

Traditional dining flows involve repetitive human effort, delays and miscommunication, limited personalization, and little learning from customer preferences. Smart Restaurant redesigns the journey from entry to exit to make the experience consistent, efficient, and adaptive.

## Experience Flow

1. Entry and Table Booking
   - Instant seating or advance booking.
   - AI assigns tables using party size, availability, past preferences, and occasion.

2. Intelligent Menu and AI Recommendations
   - Menu via mobile, table display, or projection.
   - Recommendations based on taste history, dietary needs, regional popularity, and time of day.

3. Interactive Kitchen Experience
   - Live video call with chefs for customization, ingredients, and allergies.

4. Immersive Dining Ambience
   - Occasion-based themes projected on the table.
   - Lighting and visuals adapt dynamically.

5. Automated Food Delivery
   - Robots deliver food to tables.
   - Staff focus on hospitality.

6. Smart Feedback and Learning
   - Seamless feedback collection.
   - Improves future recommendations for each guest.

## Problems Solved

- Reduces repetitive human tasks.
- Minimizes wait times and errors.
- Delivers consistent experience globally.
- Enhances customer engagement.
- Enables deep personalization.
- Improves operational efficiency.

## Current Tech Stack

We are keeping the stack simple for fast iteration and local Wi-Fi deployment.

- Frontend: React for table UI and staff dashboard.
- Backend: Python (FastAPI) for APIs + WebSocket server.
- AI: Python services (same stack or separate service).
- Optional later: Java service only for high-throughput enterprise integrations.

## Future Scope

- Multi-language global support.
- Integration with food delivery platforms.
- Nutrition tracking and health recommendations.
- Franchise-ready deployment model.
- AI-driven kitchen optimization.

## Repo Structure

- `Backend` for APIs, AI services, and orchestration.
- `Frontend` for customer and staff apps.

## Quick Start (Local Wi-Fi MVP)

Single command (server + PWA):

```bash
python launch_app.py
```

Non-technical launch (double-click):

- Windows: `run.bat`
- macOS: `run.command` (may need right click -> Open once)
- Linux: `run.sh`

Backend:

```bash
cd Backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend (React PWA, bundled locally):

Open the app at:

- Landing: `http://127.0.0.1:8000/app/#/landing`
- Customer: `http://127.0.0.1:8000/app/#/customer`
- Admin: `http://127.0.0.1:8000/app/#/admin`
- Kitchen: `http://127.0.0.1:8000/app/#/kitchen`

PWA file layout:

- `Frontend/app/views/landing.jsx`
- `Frontend/app/views/customer.jsx`
- `Frontend/app/views/admin.jsx`
- `Frontend/app/views/kitchen.jsx`
- `Frontend/app/shared/shared.jsx`
- `Frontend/app/app.jsx`

Default credentials:

- Customer login: `demo` / `demo123`
- Admin login: `admin` / `admin123`

Customer registration:

- Use the Register button on the customer screen to create a new user.

Admin ERP:

- Users, menu, inventory, billing, and orders are inside the admin view.

Real-time orders:

- Customers place orders in the Customer view.
- Admin updates order status in the Admin view.
- Chefs see filtered orders in the Kitchen view based on specialty.
- Orders auto-assign to chefs by item category; admin can override.

Auth hardening:

- Passwords are hashed (PBKDF2) and tokens expire after 1 hour.

Recommendations:

- Customer view includes AI recommendations and preferences.

Billing and ratings:

- Checkout simulates payment and logs in billing.
- Customers can rate served orders.
- Live updates flow via WebSocket `/ws/orders`.

Customer auto-discovery (on each customer machine):

```bash
python Frontend/scripts/launch_customer.py
```

Admin auto-discovery (on any admin machine):

```bash
python Frontend/scripts/launch_admin.py
```

## Vision

Smart Restaurant aims to become the standard operating system for restaurants, redefining hospitality by combining technology, personalization, and efficiency without removing the human touch.
