CREATE TABLE account (
    id SERIAL PRIMARY KEY,
    login TEXT NOT NULL,
    password TEXT NOT NULL,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX idx_account_login ON account(login);
