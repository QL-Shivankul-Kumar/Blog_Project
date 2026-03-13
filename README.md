# Blog Platform API

A REST API built with Django REST Framework for a multi-role blog platform supporting user auth, blog management, topic categorization, comments, and subscriber notifications.

**Stack:** Django 5.2 · Django REST Framework · SimpleJWT · MySQL · Pillow

---

## Setup

```bash
git clone https://github.com/yourusername/blog-platform.git
cd blog-platform/blog_project

python -m venv venv
venv\scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Create `.env` next to `manage.py`:
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=blog_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306
DEFAULT_FROM_EMAIL=noreply@blogplatform.com
FRONTEND_URL=http://localhost:3000
```

```bash
python manage.py makemigrations users
python manage.py makemigrations blog
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API runs at `http://localhost:8000`

---

## Authentication

Protected routes require a Bearer token in the header:
```
Authorization: Bearer <access_token>
```
Access token lifetime: **1 day** · Refresh token lifetime: **2 days**

---

## Roles & Workflow

```
Developer → createsuperuser via CLI
Admin     → promotes readers to author or admin via API
Author    → creates topics, writes and publishes blogs
Reader    → reads blogs, comments, subscribes to authors
```

All users register as `reader` by default. Only an admin can change roles.

---

## API Reference

Base URL: `http://localhost:8000`

---

### AUTH

---

#### `POST /api/auth/register/`
**Auth:** None

Registers a new user. Role is always set to `reader` — users cannot choose their own role. Returns access and refresh tokens on success so the user is logged in immediately after registration.

```json
Request:
{
    "email": "user@gmail.com",
    "username": "shiva",
    "first_name": "Shiva",
    "last_name": "Kumar",
    "password": "pass1234",
    "confirm_password": "pass1234"
}

Response 201:
{
    "success": true,
    "message": "Registration successful.",
    "data": {
        "id": 1,
        "email": "user@gmail.com",
        "username": "shiva",
        "role": "reader",
        "access_token": "eyJ...",
        "refresh_token": "eyJ..."
    }
}
```

---

#### `POST /api/auth/login/`
**Auth:** None

Authenticates a user with email and password. Returns JWT tokens. The access token contains `user_id`, `role`, and `email` in its payload — useful for the frontend to read role without an extra API call.

```json
Request:
{
    "email": "user@gmail.com",
    "password": "pass1234"
}

Response 200:
{
    "success": true,
    "message": "Login successful.",
    "data": {
        "id": 1,
        "email": "user@gmail.com",
        "username": "shiva",
        "role": "reader",
        "access_token": "eyJ...",
        "refresh_token": "eyJ..."
    }
}
```

---

#### `POST /api/auth/logout/`
**Auth:** Bearer token required

Blacklists the refresh token so it can never be used again to generate new access tokens. The user is effectively logged out.

```json
Request:
{
    "refresh_token": "eyJ..."
}

Response 200:
{
    "success": true,
    "message": "Logged out successfully."
}
```

---

#### `POST /api/auth/refresh/`
**Auth:** None

Takes an existing refresh token and returns a new access token. Use this when the access token expires after 1 day.

```json
Request:
{
    "refresh_token": "eyJ..."
}

Response 200:
{
    "success": true,
    "data": {
        "access_token": "eyJ..."
    }
}
```

---

#### `POST /api/auth/forgot-password/`
**Auth:** None

Sends a password reset link to the email. If the email is not registered, the response is identical — this prevents attackers from finding out which emails are registered (email enumeration protection). Reset token expires in 15 minutes.

```json
Request:
{
    "email": "user@gmail.com"
}

Response 200:
{
    "success": true,
    "message": "If an account with this email exists, a reset link has been sent."
}
```

---

#### `POST /api/auth/reset-password/`
**Auth:** None

Resets the password using the UUID token from the reset email link. Token is single-use — once used it is invalidated. All other pending tokens for the same user are also invalidated.

```json
Request:
{
    "token": "uuid-from-reset-link",
    "new_password": "newpass1234",
    "confirm_password": "newpass1234"
}

Response 200:
{
    "success": true,
    "message": "Password reset successful. You can now log in."
}
```

---

#### `PATCH /api/auth/change-password/`
**Auth:** Bearer token required

Changes password for the currently logged in user. Requires the current password as verification before setting the new one.

```json
Request:
{
    "old_password": "pass1234",
    "new_password": "newpass1234",
    "confirm_new_password": "newpass1234"
}

Response 200:
{
    "success": true,
    "message": "Password changed. Please log in again."
}
```

---

### USERS

---

#### `GET /api/users/`
**Auth:** Admin only

Returns a list of all active users in the system. Admin can optionally filter by role using a query param. Regular users cannot access this endpoint.

```
GET /api/users/?role=author    ← filter by role (optional)

Response 200:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "email": "user@gmail.com",
            "username": "shiva",
            "role": "author",
            "is_active": true,
            "is_staff": false,
            "created_at": "2026-01-01T00:00:00Z"
        }
    ]
}
```

---

#### `GET /api/users/profile/`
**Auth:** Bearer token required

Returns the full profile of the currently logged in user. Shortcut so the frontend doesn't need to know the user's ID.

```json
Response 200:
{
    "success": true,
    "data": {
        "id": 1,
        "email": "user@gmail.com",
        "username": "shiva",
        "first_name": "Shiva",
        "last_name": "Kumar",
        "role": "reader",
        "bio": "",
        "profile_pic": null,
        "is_active": true,
        "created_at": "2026-01-01T00:00:00Z"
    }
}
```

---

#### `GET /api/users/:id/`
**Auth:** Bearer token required

Returns a user's profile by ID. If the requester is viewing their own profile or is an admin, full details are shown. Otherwise only public fields like username, bio, and role are returned.

```json
Response 200:
{
    "success": true,
    "data": {
        "id": 2,
        "username": "john",
        "first_name": "John",
        "role": "author",
        "bio": "I write about tech",
        "profile_pic": null
    }
}
```

---

#### `PATCH /api/users/:id/`
**Auth:** Own account or Admin

Updates a user's profile. Users can update their own `username`, `first_name`, `last_name`, `bio`, and `profile_pic`. The `role` field is read-only here — role changes go through the dedicated role endpoint.

```json
Request:
{
    "first_name": "Shiva",
    "bio": "I love writing"
}

Response 200:
{
    "success": true,
    "message": "Profile updated.",
    "data": { "...updated profile..." }
}
```

---

#### `DELETE /api/users/:id/`
**Auth:** Own account or Admin

Permanently deletes the user account. Their blogs remain in the database with `author` set to `null` and shown as `Deleted User` in responses.

```json
Response 204:
{
    "success": true,
    "message": "Account deleted."
}
```

---

#### `PATCH /api/users/:id/role/`
**Auth:** Admin only

Changes the role of any user. This is the only way roles can be assigned — users cannot self-assign roles. Promoting to `admin` also grants `is_staff` access to the Django admin panel. Superuser status is never granted via this endpoint.

```json
Request:
{
    "role": "author"
}

Valid values: reader · author · admin

Response 200:
{
    "success": true,
    "message": "shiva's role changed to 'author'.",
    "data": { "...updated user..." }
}
```

---

### SUBSCRIPTIONS

---

#### `GET /api/subscriptions/my/`
**Auth:** Bearer token required

Returns all authors the currently logged in user is subscribed to (following).

```json
Response 200:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "subscriber": { "id": 1, "username": "shiva" },
            "author": { "id": 2, "username": "john" },
            "subscribed_at": "2026-01-01T00:00:00Z"
        }
    ]
}
```

---

#### `GET /api/subscriptions/author/:id/`
**Auth:** Bearer token required

Returns all subscribers (followers) of a specific author. Only works if the user with that ID has the `author` role — returns 404 otherwise.

```json
Response 200:
{
    "success": true,
    "data": [ "...list of subscription objects..." ]
}
```

---

#### `POST /api/subscriptions/:author_id/`
**Auth:** Bearer token required

Subscribes the logged in user to an author. The ID in the URL is the author's user ID. Users cannot subscribe to themselves or to non-authors. Duplicate subscriptions are blocked.

```
No request body needed.

Response 201:
{
    "success": true,
    "message": "Subscribed to john.",
    "data": { "...subscription object..." }
}
```

---

#### `DELETE /api/subscriptions/:author_id/`
**Auth:** Bearer token required

Unsubscribes the logged in user from an author. Returns 404 if the subscription does not exist.

```json
Response 200:
{
    "success": true,
    "message": "Unsubscribed from john."
}
```

---

### TOPICS

---

#### `GET /api/topics/`
**Auth:** None

Returns all topics with a count of their published blogs. Open to everyone including unauthenticated users.

```json
Response 200:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Technology",
            "slug": "technology",
            "blog_count": 5,
            "created_by": { "id": 2, "username": "shiva" },
            "created_at": "2026-01-01T00:00:00Z"
        }
    ]
}
```

---

#### `POST /api/topics/`
**Auth:** Author or Admin

Creates a new topic. Slug is auto-generated from the name. Duplicate topic names (even with different casing) are rejected. The `created_by` field is set automatically from the logged in user.

```json
Request:
{
    "name": "Technology"
}

Response 201:
{
    "success": true,
    "message": "Topic created.",
    "data": {
        "id": 1,
        "name": "Technology",
        "slug": "technology"
    }
}
```

---

#### `GET /api/topics/:id/`
**Auth:** None

Returns a single topic along with all its published blogs. Open to everyone.

```json
Response 200:
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Technology",
        "slug": "technology",
        "blogs": [ "...list of published blogs under this topic..." ]
    }
}
```

---

#### `DELETE /api/topics/:id/`
**Auth:** Admin only

Permanently deletes a topic. If any blogs exist under this topic, deletion is blocked and returns a 409 Conflict — blogs must be reassigned or deleted first.

```json
Response 204:
{ "success": true, "message": "Topic deleted." }

Response 409 (if blogs exist):
{ "success": false, "message": "Cannot delete — blogs exist under this topic." }
```

---

### BLOGS

---

#### `GET /api/blogs/`
**Auth:** None

Returns all published blogs. Supports optional title search via query param. Open to everyone.

```
GET /api/blogs/?title=django    ← search by title (optional)

Response 200:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "title": "My First Blog",
            "slug": "my-first-blog",
            "is_published": true,
            "view_count": 10,
            "published_at": "2026-01-01T00:00:00Z",
            "author": { "id": 2, "username": "shiva" },
            "topic": { "id": 1, "name": "Technology" }
        }
    ]
}
```

---

#### `POST /api/blogs/`
**Auth:** Author or Admin

Creates a new blog. Slug is auto-generated from the title and guaranteed unique. `topic_id` accepts the integer ID of an existing topic. If `is_published` is set to `true` on creation, all subscribers of the author are notified by email immediately.

```json
Request:
{
    "title": "My First Blog",
    "content": "Blog content here...",
    "topic_id": 1,
    "is_published": false
}

Response 201:
{
    "success": true,
    "message": "Blog created.",
    "data": {
        "id": 1,
        "title": "My First Blog",
        "slug": "my-first-blog",
        "content": "Blog content here...",
        "is_published": false,
        "view_count": 0,
        "author": { "...author details..." },
        "topic": { "...topic details..." }
    }
}
```

---

#### `GET /api/blogs/:id/`
**Auth:** None (published) · Bearer token (own draft)

Returns full blog detail including content. Unpublished blogs are only visible to the author and admin. View count increments on every request except when the author views their own blog.

```json
Response 200:
{
    "success": true,
    "data": {
        "id": 1,
        "title": "My First Blog",
        "slug": "my-first-blog",
        "content": "...",
        "is_published": true,
        "view_count": 11,
        "author": { "...author details..." },
        "topic": { "...topic details..." },
        "published_at": "2026-01-01T00:00:00Z"
    }
}
```

---

#### `GET /api/blogs/slug/:slug/`
**Auth:** None (published) · Bearer token (own draft)

Same as Get Blog by ID but looks up by slug instead of ID. Useful for SEO-friendly URLs on the frontend.

```
GET /api/blogs/slug/my-first-blog/

Response 200: same structure as Get Blog by ID
```

---

#### `PATCH /api/blogs/:id/`
**Auth:** Author (own blog) or Admin

Updates blog fields. Send only the fields you want to change. If the blog transitions from draft to published via this update, subscriber emails are sent automatically.

```json
Request (send only fields to update):
{
    "title": "Updated Title",
    "content": "Updated content...",
    "topic_id": 2
}

Response 200:
{
    "success": true,
    "message": "Blog updated.",
    "data": { "...updated blog..." }
}
```

---

#### `DELETE /api/blogs/:id/`
**Auth:** Author (own blog) or Admin

Permanently deletes a blog and all its comments.

```json
Response 204:
{
    "success": true,
    "message": "Blog deleted."
}
```

---

#### `PATCH /api/blogs/:id/publish/`
**Auth:** Author (own blog) or Admin

Toggles the published state of a blog. When a blog transitions from draft to published, all subscribers of the author receive an email notification in the background. Unpublishing does not trigger any emails.

```json
Request:
{ "is_published": true }    ← publish
{ "is_published": false }   ← unpublish

Response 200:
{
    "success": true,
    "message": "Blog published.",
    "data": { "...blog with updated status..." }
}
```

---

#### `GET /api/users/:id/blogs/`
**Auth:** None (published only) · Bearer token — own account or Admin (all including drafts)

Returns all blogs by a specific author. Unauthenticated users only see published blogs. The author and admin can also see drafts by passing `?is_published=false`.

```
GET /api/users/2/blogs/                    ← published blogs only
GET /api/users/2/blogs/?is_published=false ← drafts only (own account or admin)

Response 200:
{
    "success": true,
    "data": [ "...list of blogs..." ]
}
```

---

### COMMENTS

---

#### `GET /api/blogs/:blog_id/comments/`
**Auth:** None

Returns all active (non-deleted) comments on a published blog, ordered oldest first.

```json
Response 200:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "user": { "id": 3, "username": "abhisek" },
            "content": "Great post!",
            "created_at": "2026-01-01T00:00:00Z"
        }
    ]
}
```

---

#### `POST /api/blogs/:blog_id/comments/`
**Auth:** Bearer token required (any logged in user)

Adds a comment to a published blog. Only works on published blogs — commenting on drafts is not allowed. Comment cannot be empty or exceed 2000 characters.

```json
Request:
{
    "content": "Great post!"
}

Response 201:
{
    "success": true,
    "message": "Comment added.",
    "data": { "...comment object..." }
}
```

---

#### `PATCH /api/blogs/:blog_id/comments/:comment_id/`
**Auth:** Comment owner only

Edits the content of a comment. Only the user who wrote the comment can edit it — not even the blog author or admin.

```json
Request:
{
    "content": "Updated comment text"
}

Response 200:
{
    "success": true,
    "message": "Comment updated.",
    "data": { "...updated comment..." }
}
```

---

#### `DELETE /api/blogs/:blog_id/comments/:comment_id/`
**Auth:** Comment owner · Blog author · Admin

Soft-deletes a comment — it is marked as deleted and hidden from responses but kept in the database. Three roles can delete: the user who wrote it, the author of the blog it belongs to, or any admin.

```json
Response 200:
{
    "success": true,
    "message": "Comment deleted."
}
```

---

## Response Format

**Success**
```json
{
    "success": true,
    "message": "...",
    "data": {}
}
```

**Error**
```json
{
    "success": false,
    "message": "...",
    "errors": {}
}
```

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created |
| `204` | Deleted |
| `400` | Validation error |
| `401` | Not authenticated |
| `403` | Forbidden |
| `404` | Not found |
| `409` | Conflict |