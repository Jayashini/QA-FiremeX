# FiremeX Routes

This document lists the application routes defined in `frontend/src/routes/index.tsx`.

## Public / auth routes

| Path | Component | Access | Notes |
| --- | --- | --- | --- |
| `/FiremeX/register` | `RegisterGateway` | Public | Rendered inside `AuthLayout` with `max-w-[800px]`. |
| `/FiremeX/login` | `Login` | Public | Rendered inside `AuthLayout`. |
| `/` | `Login` | Public | Normalized to `/FiremeX/login` by `normalizePath()`. |

## Admin routes

These routes require a logged-in user and enforce `user.role === 'admin'`.

| Path | Component | Access | Notes |
| --- | --- | --- | --- |
| `/FiremeX/admin/dashboard` | `Dashboard` | Admin | Wrapped in `AdminLayout` with `activePage="dashboard"`. |
| `/FiremeX/admin/incidents` | `Incidents` | Admin | Wrapped in `AdminLayout` with `activePage="incidents"`. |
| `/FiremeX/admin/alerts` | `Alerts` | Admin | Wrapped in `AdminLayout` with `activePage="alerts"`. |
| `/FiremeX/admin/livefeed` | `Livefeed` | Admin | Wrapped in `AdminLayout` with `activePage="livefeed"`. |
| `/FiremeX/admin/livefeed/add-device` | `AddDevice` | Admin | Same layout as livefeed, used for the add-device flow. |
| `/FiremeX/admin/users` | `User` | Admin | Wrapped in `AdminLayout` with `activePage="users"`. |
| `/FiremeX/admin/profile` | `Profile` | Admin | Wrapped in `AdminLayout` with `activePage="profile"`. |
| `/FiremeX/admin/settings` | `Settings` | Admin | Wrapped in `AdminLayout` with `activePage="settings"`. |

## Operator routes

These routes require a logged-in user and enforce `user.role === 'operator'`.

| Path | Component | Access | Notes |
| --- | --- | --- | --- |
| `/FiremeX/operator/livefeed` | `Livefeed` | Operator | Wrapped in `OperatorLayout` with `activePage="livefeed"` and `readOnly`. |
| `/FiremeX/operator/incidents` | `Incidents` | Operator | Wrapped in `OperatorLayout` with `activePage="incidents"`. |
| `/FiremeX/operator/profile` | `Profile` | Operator | Wrapped in `OperatorLayout` with `activePage="profile"`. |

## Route behavior summary

- `normalizePath(pathname)` converts empty or `/` paths into `/FiremeX/login`.
- It also strips a trailing slash from a pathname.
- If a protected admin/operator path is accessed without a valid session, the app redirects to `/FiremeX/login`.
- If the logged-in user tries to access a route for the wrong role, the app redirects to `homePathFor(user)`.
- Any unmatched path falls back to the login page.

## Route tree

```text
/FiremeX
├── /login
├── /register
├── /admin
│   ├── /dashboard
│   ├── /incidents
│   ├── /alerts
│   ├── /livefeed
│   │   └── /add-device
│   ├── /users
│   ├── /profile
│   └── /settings
└── /operator
    ├── /livefeed
    ├── /incidents
    └── /profile
```
