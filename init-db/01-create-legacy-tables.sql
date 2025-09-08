-- Create tables matching your legacy database schema
-- Modify these to match your actual legacy database structure

-- Users table
CREATE TABLE IF NOT EXISTS user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    admin_ind CHAR(1) DEFAULT 'N' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_admin (admin_ind)
);

-- TLog table
CREATE TABLE IF NOT EXISTS tlog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trig_id INT NOT NULL,
    log_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trig_id (trig_id)
);

-- Insert some sample data for testing
INSERT INTO user (email, password_hash, admin_ind) VALUES
('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5w6iuF.Tay', 'Y'),
('user@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5w6iuF.Tay', 'N');

INSERT INTO tlog (trig_id, log_data) VALUES
(1, 'Sample log entry 1'),
(1, 'Sample log entry 2'),
(1, 'Sample log entry 3'),
(2, 'Sample log entry for trig 2'),
(2, 'Another sample log entry for trig 2'),
(3, 'Sample log entry for trig 3');
