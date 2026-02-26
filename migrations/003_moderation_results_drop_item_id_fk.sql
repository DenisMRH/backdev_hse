-- Убираем FK на advertisements(id), чтобы API мог создавать задачи для любого item_id.
-- Воркер при отсутствии объявления отправит сообщение в DLQ.
ALTER TABLE moderation_results
    DROP CONSTRAINT IF EXISTS moderation_results_item_id_fkey;
