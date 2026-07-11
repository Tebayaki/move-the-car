# 🚗 挪车码 (Move the Car)

A minimal web app that lets anyone scan a QR code to notify the car owner via [Server酱³](https://sc3.ft07.com/) push notification.

## Quick Start

### 1. Get a SENDKEY

1. Register at [sct.ftqq.com](https://sct.ftqq.com) with your WeChat.
2. Copy your **SendKey** from the dashboard.

### 2. Run with Docker

```bash
# Build and start (replace YOUR_SENDKEY with your actual key)
SENDKEY=your_send_key_here docker compose up -d
```

The app will be available at `http://localhost:5000`.

### 3. Run without Docker

```bash
pip install -r requirements.txt
SENDKEY=your_send_key_here python app.py
```

## Usage

- Place the QR code (pointing to your deployed URL) on your car dashboard.
- When someone scans it, they tap the big **挪车通知** button.
- You receive a Server酱 push notification on your phone with the timestamp and visitor's IP.
- The button is rate-limited to one click per 30 seconds per IP to prevent spam.

## Deployment Notes

- For production, put it behind **nginx/caddy** with HTTPS so the QR code works over the web.
- The app listens on port **5000** by default.
- The button works best on mobile — the UI is designed for window-side operation.
