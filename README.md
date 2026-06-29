# FlowSpec Manual Blocking Portal

A web-based portal for manually managing BGP FlowSpec rules integrated with ExaBGP and FastNetMon.

## Features

- 🎯 Create, view, and delete FlowSpec blocking rules
- 🔍 Filter rules by IP, subnet, protocol, port
- ⏱️ Set rule expiration/TTL
- 📋 Audit logs for all rule changes
- 🔐 User authentication and authorization
- 🧪 Dry-run preview before applying rules
- 📊 Dashboard with active rules overview

## Architecture

```
FlowSpec Portal (Web UI)
        ↓
  Flask API Backend
        ↓
  ExaBGP Client / FastNetMon API
        ↓
  ExaBGP / FastNetMon
        ↓
  BGP Routers (FlowSpec Rules)
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- ExaBGP configured and running
- FastNetMon (optional, for auto-detection)
- Python 3.9+ (for local development)
- Node.js 16+ (for frontend development)

### Using Docker Compose

```bash
docker-compose up -d
```

Access the portal at `http://localhost:3000`

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

Edit `.env` or `backend/config.py`:

```env
EXABGP_HOST=localhost
EXABGP_PORT=6001
FASTNETMON_API_URL=http://localhost:8080
DATABASE_URL=sqlite:///flowspec.db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/register` - Register new user (admin only)

### Rules Management
- `POST /api/rules` - Create a new FlowSpec rule
- `GET /api/rules` - List all rules
- `GET /api/rules/<id>` - Get rule details
- `PUT /api/rules/<id>` - Update a rule
- `DELETE /api/rules/<id>` - Delete/withdraw a rule
- `POST /api/rules/<id>/deploy` - Deploy a rule
- `POST /api/rules/<id>/withdraw` - Withdraw a rule

### Dashboard
- `GET /api/dashboard/stats` - Get overview statistics
- `GET /api/dashboard/active-rules` - Get active rules

### Audit Logs
- `GET /api/audit-logs` - View audit trail
- `GET /api/audit-logs?rule_id=<id>` - Get logs for specific rule

## Rule Example

```json
{
  "name": "Block DDoS Source",
  "description": "Block traffic from suspicious IP",
  "destination_ip": "192.0.2.1/32",
  "source_ip": "198.51.100.0/24",
  "protocol": "tcp",
  "destination_port": "80,443",
  "action": "discard",
  "ttl_minutes": 60
}
```

## Testing

```bash
cd backend
pytest tests/
```

## Supported Actions

- **discard** - Drop all matching traffic
- **accept** - Allow matching traffic (whitelist)
- **rate-limit** - Rate limit matching traffic

## Supported Match Criteria

- Source IP/subnet (CIDR)
- Destination IP/subnet (CIDR)
- Protocol (tcp, udp, icmp, etc.)
- Source Port (single or comma-separated)
- Destination Port (single or comma-separated)
- DSCP (Differentiated Services Code Point)
- Fragment Offset

## License

MIT
