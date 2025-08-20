-- Initialize the hyperfunnel database
-- This script runs automatically when the PostgreSQL container starts

-- Create the main database if it doesn't exist
-- (PostgreSQL creates it automatically from environment variables)

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create hotels table
CREATE TABLE IF NOT EXISTS hotels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    stars INTEGER,
    images TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    images TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE hyperfunnel TO hyperfunnel_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hyperfunnel_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hyperfunnel_user;
