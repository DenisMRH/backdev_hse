CREATE TABLE moderation_results (
    id SERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES advertisements(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_violation BOOLEAN,
    probability FLOAT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_moderation_results_item_id ON moderation_results(item_id);
CREATE INDEX idx_moderation_results_status ON moderation_results(status);
