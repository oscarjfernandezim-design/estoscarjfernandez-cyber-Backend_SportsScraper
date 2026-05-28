DROP TABLE IF EXISTS user_favorites CASCADE;
DROP TABLE IF EXISTS product_prices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL UNIQUE,
    brand VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_prices (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    store_name VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    product_url TEXT NOT NULL,
    scraped_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- NUEVA TABLA: Conecta qué usuario guardó qué producto
CREATE TABLE user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    -- Esto evita que un usuario guarde el mismo producto dos veces como favorito
    CONSTRAINT unique_user_product UNIQUE (user_id, product_id)
);

-- Alerts table will store price alerts for users
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    product_id INT NOT NULL,
    target_price NUMERIC(12,2) NOT NULL,
    stores JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);