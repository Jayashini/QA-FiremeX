# FiremeX database schema

## Database

- **Default database name:** `firemex` (set with `DB_NAME`; a full `DATABASE_DSN` can override the connection settings).
- **Database engine:** PostgreSQL.
- **Tables:** `organizations`, `users`, `cameras`, and `incidents`.
- **Source of schema:** GORM models migrated on backend startup. A deployed database may differ if it was configured with a different DSN or modified independently.
- **Type notation:** PostgreSQL types. `timestamptz` means timestamp with time zone. Nullable columns permit `NULL`.

## `organizations`

Defined in [`backend/models/organization.go`](backend/models/organization.go). The `id`, `created_at`, `updated_at`, and `deleted_at` fields are inherited from GORM's `gorm.Model`.

| Column | PostgreSQL type | Nullability / default | Key / notes |
|---|---|---|---|
| `id` | `bigserial` | Not null; auto-generated | **Primary key** |
| `created_at` | `timestamptz` | Nullable | |
| `updated_at` | `timestamptz` | Nullable | |
| `deleted_at` | `timestamptz` | Nullable | Indexed; used for soft deletion |
| `name` | `text` | Not null | |
| `code` | `text` | Not null | Unique |
| `sector` | `text` | Not null | |
| `email` | `text` | Not null | |
| `phone` | `text` | Nullable | |
| `country` | `text` | Nullable | |

## `users`

Defined in [`backend/models/user.go`](backend/models/user.go).

| Column | PostgreSQL type | Nullability / default | Key / notes |
|---|---|---|---|
| `id` | `bigserial` | Not null; auto-generated | **Primary key** |
| `created_at` | `timestamptz` | Nullable | |
| `updated_at` | `timestamptz` | Nullable | |
| `deleted_at` | `timestamptz` | Nullable | Indexed; used for soft deletion |
| `name` | `text` | Not null | |
| `email` | `text` | Not null | Unique |
| `password` | `text` | Not null | |
| `role` | `text` | Nullable; default `'operator'` | |
| `status` | `text` | Nullable; default `'pending'` | |
| `organization_id` | `bigint` | Nullable | **Foreign key** → `organizations.id` |

## `cameras`

Defined in [`backend/models/camera.go`](backend/models/camera.go).

| Column | PostgreSQL type | Nullability / default | Key / notes |
|---|---|---|---|
| `id` | `bigserial` | Not null; auto-generated | **Primary key** |
| `created_at` | `timestamptz` | Nullable | |
| `updated_at` | `timestamptz` | Nullable | |
| `deleted_at` | `timestamptz` | Nullable | Indexed; used for soft deletion |
| `entity_id` | `text` | Not null | |
| `source_type` | `text` | Not null; default `'home_assistant'` | |
| `display_name` | `text` | Not null | |
| `zone` | `text` | Nullable | |
| `ai_enabled` | `boolean` | Nullable; default `false` | |
| `organization_id` | `bigint` | Not null | **Foreign key** → `organizations.id` |

## `incidents`

Defined in [`backend/models/incident.go`](backend/models/incident.go). This model does not use GORM soft deletion, so it has no `deleted_at` column.

| Column | PostgreSQL type | Nullability / default | Key / notes |
|---|---|---|---|
| `review_status` | `text` | Not null; default `'unconfirmed'` | |
| `sample_id` | `text` | Nullable | |
| `idempotency_key` | `text` | Nullable | Unique index |
| `observed_at` | `timestamptz` | Nullable | |
| `model_version` | `text` | Nullable | |
| `threshold_used` | `double precision` | Nullable | |
| `evidence_status` | `text` | Not null; default `'missing'` | |
| `evidence_expires_at` | `timestamptz` | Nullable | |
| `id` | `bigserial` | Not null; auto-generated | **Primary key** |
| `created_at` | `timestamptz` | Nullable | Indexed with `camera_id` and `organization_id` |
| `updated_at` | `timestamptz` | Nullable | |
| `organization_id` | `bigint` | Not null | **Foreign key** → `organizations.id` |
| `camera_id` | `bigint` | Not null | **Foreign key** → `cameras.id` |
| `camera_name` | `text` | Not null | |
| `zone` | `text` | Nullable | |
| `class` | `text` | Not null | |
| `confidence` | `double precision` | Not null | |
| `detections` | `text` | Nullable | |
| `snapshot_file` | `text` | Nullable | |
| `status` | `text` | Not null; default `'unresolved'` | |
| `resolve_note` | `text` | Nullable | |
| `blocker_reason` | `text` | Nullable | |
| `resolved_by_id` | `bigint` | Nullable | **Foreign key** → `users.id` |
| `resolved_at` | `timestamptz` | Nullable | |

## Foreign keys

| Table | Column | References |
|---|---|---|
| `users` | `organization_id` | `organizations.id` |
| `cameras` | `organization_id` | `organizations.id` |
| `incidents` | `organization_id` | `organizations.id` |
| `incidents` | `camera_id` | `cameras.id` |
| `incidents` | `resolved_by_id` | `users.id` |

The model definitions do not specify custom foreign-key delete or update actions.
