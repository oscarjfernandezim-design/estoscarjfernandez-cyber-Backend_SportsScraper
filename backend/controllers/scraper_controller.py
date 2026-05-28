from flask import jsonify
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_scraper_handler():
    """
    Execute scraping for all brands and categories.
    Returns summary of scraped products.
    """
    try:
        summary = {
            'total_products': 0,
            'brands': {},
            'error': None
        }
        
        # lazy import scraper functions to avoid importing heavyweight scraping
        # libraries at app startup (they may require extra system deps)
        try:
            from backend.scraper.scrappy_adidad import scrape_brand_category, save_products_to_db, CATEGORIES
        except Exception as e:
            error_msg = f"Scraper libs not available: {e}"
            print(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 500

        brands = ['adidas', 'nike', 'puma']
        all_products = []
        
        print("\n=== INICIANDO SCRAPER ===\n")
        
        for brand in brands:
            summary['brands'][brand] = {
                'categories': {}
            }
            
            for category in CATEGORIES[:3]:  # Limit to first 3 categories for speed
                try:
                    print(f"Scraping {brand} / {category}...")
                    
                    # Scrape category with limited items for testing
                    products, source_url = scrape_brand_category(
                        brand, 
                        category, 
                        max_items=5,  # Keep it small for testing
                        pages=1
                    )
                    
                    if products:
                        count = len(products)
                        summary['brands'][brand]['categories'][category] = count
                        all_products.extend(products)
                        print(f"  ✓ {count} productos encontrados")
                    else:
                        summary['brands'][brand]['categories'][category] = 0
                        print(f"  ✗ Sin resultados")
                        
                except Exception as e:
                    error_msg = str(e)[:100]
                    summary['brands'][brand]['categories'][category] = f"error: {error_msg}"
                    print(f"  ✗ Error: {error_msg}")
        
        # Save all products to database
        if all_products:
            print(f"\nGuardando {len(all_products)} productos en BD...")
            saved_count = save_products_to_db(all_products)
            summary['total_products'] = saved_count
            print(f"✓ {saved_count} productos guardados exitosamente\n")
        else:
            summary['total_products'] = 0
            print("\n✗ No se encontraron productos para guardar\n")
        
        return jsonify({
            'success': True,
            'message': 'Scraping completado',
            'summary': summary
        }), 200
        
    except Exception as e:
        error_msg = f"Error ejecutando scraper: {str(e)}"
        print(f"✗ {error_msg}\n")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


def health_check_handler():
    """Health check for scraper endpoint"""
    # Check if scraper dependencies are importable
    try:
        from backend.scraper.scrappy_adidad import CATEGORIES  # type: ignore
        scraper_available = True
    except Exception:
        scraper_available = False

    return jsonify({
        'status': 'ok',
        'scraper_available': scraper_available
    }), 200
