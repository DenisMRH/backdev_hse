CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE advertisements (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category INTEGER NOT NULL,
    images_qty INTEGER NOT NULL
);

CREATE INDEX idx_advertisements_user_id ON advertisements(user_id);