import os
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from backend.database.db import get_connection

load_dotenv()

def run_schema():
    schema_path = pathlib.Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Ejecutar el archivo SQL para crear las tablas vacías
            print("Creando tablas en la base de datos...")
            cur.execute(sql)
            
            # 2. Insertar los datos de prueba de forma separada y segura
            print("Insertando usuarios de prueba...")
            insert_users = """
            INSERT INTO users (full_name, email, password)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO NOTHING;
            """
            # Insertamos los dos usuarios uno por uno
            cur.execute(insert_users, ('Ana Torres', 'ana@example.com', 'clave123'))
            cur.execute(insert_users, ('Luis Perez', 'luis@example.com', 'password456'))
            
            # 3. Insertar productos de prueba
            print("Insertando productos de prueba...")
            insert_products = """
            INSERT INTO products (product_name, brand, category, image_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_name) DO NOTHING
            RETURNING id;
            """
            
            test_products = [
                ('Nike Air Max 90', 'Nike', 'Running', 'https://via.placeholder.com/600x600?text=Nike+Air+Max+90'),
                ('Adidas Ultraboost 22', 'Adidas', 'Running', 'https://via.placeholder.com/600x600?text=Adidas+Ultraboost'),
                ('Puma RS-X Sneaker', 'Puma', 'Lifestyle', 'https://via.placeholder.com/600x600?text=Puma+RS-X'),
                ('Nike Dri-FIT T-Shirt', 'Nike', 'Apparel', 'https://via.placeholder.com/600x600?text=Nike+Dri-FIT'),
                ('Adidas Training Shorts', 'Adidas', 'Apparel', 'https://via.placeholder.com/600x600?text=Adidas+Shorts'),
                ('Puma Essentials Hoodie', 'Puma', 'Apparel', 'https://via.placeholder.com/600x600?text=Puma+Hoodie'),
            ]
            
            product_ids = []
            for name, brand, category, image_url in test_products:
                cur.execute(insert_products, (name, brand, category, image_url))
                result = cur.fetchone()
                if result:
                    # RealDictCursor returns a dict, otherwise a tuple/list
                    if isinstance(result, dict):
                        product_ids.append(result.get('id'))
                    else:
                        product_ids.append(result[0])
            
            # 4. Insertar precios de prueba (ofertas)
            if product_ids:
                print("Insertando precios de prueba...")
                insert_prices = """
                INSERT INTO product_prices (product_id, store_name, price, product_url)
                VALUES (%s, %s, %s, %s);
                """
                
                stores_data = [
                    (product_ids[0], 'Zalando', 129.99, 'https://zalando.es/nike-air-max-90'),
                    (product_ids[0], 'Nike Store', 134.99, 'https://nike.com/air-max-90'),
                    (product_ids[0], 'ASOS', 124.99, 'https://asos.com/nike-air-max'),
                    (product_ids[1], 'Adidas Store', 189.99, 'https://adidas.com/ultraboost-22'),
                    (product_ids[1], 'Zalando', 179.99, 'https://zalando.es/adidas-ultraboost'),
                    (product_ids[2], 'Puma Store', 109.99, 'https://puma.com/rs-x'),
                    (product_ids[2], 'ASOS', 104.99, 'https://asos.com/puma-rs-x'),
                    (product_ids[3], 'Nike Store', 34.99, 'https://nike.com/dri-fit-tee'),
                    (product_ids[4], 'Adidas Store', 39.99, 'https://adidas.com/training-shorts'),
                    (product_ids[5], 'Puma Store', 59.99, 'https://puma.com/essentials-hoodie'),
                ]
                
                for product_id, store_name, price, url in stores_data:
                    cur.execute(insert_prices, (product_id, store_name, price, url))
            
            conn.commit()
            print("Schema executed successfully!")

if __name__ == "__main__":
    run_schema()