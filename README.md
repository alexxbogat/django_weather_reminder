# Django Weather Reminder API

A Django + DRF project that allows users to register, subscribe to city weather notifications, and retrieve the latest
weather data.

---

## Authentication

This API uses **JWT** tokens via `djangorestframework-simplejwt`.

| Endpoint              | Method | Description                    |
|-----------------------|--------|--------------------------------|
| `/api/token/`         | POST   | Obtain access & refresh tokens |
| `/api/token/refresh/` | POST   | Refresh access token           |
| `/api/token/verify/`  | POST   | Verify access token            |

**Header Example for Protected Endpoints:**

```
Authorization: Bearer <access_token>
```

---

## Users

### Register a new user

**POST** `/api/register/`

**Request Body:**

```json
{
  "username": "alex",
  "email": "alex@example.com",
  "password": "securepassword"
}
```

**Response Example:**

```json
{
  "username": "alex",
  "email": "alex@example.com"
}
```

---

## Cities

### List all cities

**GET** `/api/cities/`

**Response Example:**

```json
[
  {
    "id": 1,
    "name": "Kyiv",
    "country": "UA"
  },
  {
    "id": 2,
    "name": "London",
    "country": "GB"
  }
]
```

### Get latest weather for a city

**GET** `/api/cities/{city_name}/{country_code}/weather/`

**Response Example:**

```json
{
  "city": "Kyiv, UA",
  "temperature": 22,
  "feels_like": 21,
  "humidity": 60,
  "wind_speed": 5,
  "pressure": 1012
}
```

---

## Subscriptions

> Requires authentication

### List current user's subscriptions

**GET** `/api/subscription/`

**Response Example:**

```json
[
  {
    "id": 1,
    "city": "Kyiv",
    "country": "UA",
    "email_push": true,
    "webhook_url": "https://example.com/webhook",
    "period_push": 12
  }
]
```

### Subscribe to a city

**POST** `/api/cities/{city_name}/{country_code}/weather/subscription/`

**Request Body:**

```json
{
  "email_push": true,
  "webhook_url": "https://example.com/webhook",
  "period_push": 12
}
```

**Response Example:**

```json
{
  "user": "alex",
  "email": "alex@example.com",
  "subscription": true,
  "city": "Kyiv",
  "country": "UA",
  "email_push": true,
  "webhook_url": "https://example.com/webhook",
  "period_push": 12
}
```

### Update subscription

**PUT** `/api/cities/{city_name}/{country_code}/weather/subscription/`

**Request Body:** Same as POST

**Response Example:**

```json
{
  "user": "alex",
  "email": "alex@example.com",
  "subscription": "Subscription updated",
  "city": "Kyiv",
  "country": "UA",
  "email_push": true,
  "period_push": 12
}
```

### Delete subscription

**DELETE** `/api/cities/{city_name}/{country_code}/weather/subscription/`

**Response Example:**

```json
{
  "user": "alex",
  "email": "alex@example.com",
  "subscription": "Subscription removed",
  "city": "Kyiv",
  "country": "UA"
}
```
