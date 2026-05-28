import os
import sys
from dotenv import load_dotenv

# Parche dinámico de rutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database.db import get_connection

load_dotenv()

def insert_product():
    query = """
    INSERT INTO products (product_name, brand, category, image_url) 
    VALUES (%s, %s, %s, %s) 
    ON CONFLICT (product_name) DO NOTHING;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, ('Jordan 11', 'Nike', 'Zapatillas', 'https://static.nike.com/images/jordan.png'))
            conn.commit()
            print("¡Producto 'Jordan 11' insertado con éxito en el catálogo de Docker!")

if __name__ == "__main__":
    insert_product()