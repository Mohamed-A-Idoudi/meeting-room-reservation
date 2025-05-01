# meeting-room-reservation
A DevOps project to manage meeting room bookings using microservices, Docker, Kubernetes, and CI/CD.
Initial setup complete.
## Microservices
- user-service: Manages users and roles.
- room-service: Manages rooms and availability.
- reservation-service: Handles reservations.

# Meeting Room Reservation Project
## Phase 4: Containerization with Docker and Kubernetes
- **Docker**: Built images for user-service, room-service, reservation-service; used docker-compose.yml for local testing.
- **Kubernetes**: Deployed services, PostgreSQL, Kafka, Zookeeper in Minikube; used Deployments and Services.
- **NGINX Ingress**: Configured Load Balancer to route traffic to /users, /rooms, /reservations.
- **Challenges**: Fixed database creation, Kafka crashes, webhook errors.
- **Repository**: https://github.com/Mohamed-A-Idoudi/meeting-room-reservation/tree/feature/setup

## UI Implementation (Final)
- **Technology**: React with Material-UI for a professional, responsive interface.
- **Features**:
  - Home: Welcome page with a call-to-action to book rooms.
  - Rooms: Card-based grid with availability and "Book Now" buttons.
  - Reservations: Table listing reservations with "Cancel" functionality.
  - Profile: Clean display of user details in a card layout.
- **Design**: Responsive, with loading spinners, error alerts, and no-data messages.
- **Back-End Fixes**: Resolved PostgreSQL DNS issues, updated Flask routes to fix 404 errors, and bypassed Kafka issues.
- **Testing**: Full end-to-end testing of APIs and UI ensures functionality.
