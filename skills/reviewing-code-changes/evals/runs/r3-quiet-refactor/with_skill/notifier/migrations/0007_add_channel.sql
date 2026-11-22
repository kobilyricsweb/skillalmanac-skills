-- Adds the delivery channel to notifications.
ALTER TABLE notifications ADD COLUMN channel text NOT NULL;
CREATE INDEX idx_notifications_channel ON notifications (channel);
