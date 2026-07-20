#!/usr/bin/env python3
"""
Flask API Server para Mercado Libre Tracker
Proporciona endpoints REST para el dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import json
from ml_scraper import MercadoLibreScraper

app = Flask(__name__)
CORS(app)

scraper = MercadoLibreScraper()

# Ruta para servir el dashboard
@app.route('/')
def index():
    return send_from_directory('.', 'ml_dashboard.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Obtiene todos los productos (último registro de cada uno)"""
    try:
        products = scraper.get_all_products_latest()
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/products/<product_id>/history', methods=['GET'])
def get_product_history(product_id):
    """Obtiene el historial de precios de un producto"""
    try:
        days = request.args.get('days', 30, type=int)
        history = scraper.get_price_history(product_id)
        
        # Filtrar por días si es necesario
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            history = [h for h in history if h['timestamp'] >= cutoff_date]
        
        return jsonify({
            'success': True,
            'product_id': product_id,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtiene las alertas recientes"""
    try:
        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        
        days = request.args.get('days', 7, type=int)
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT * FROM price_alerts 
            WHERE triggered_at >= ? 
            ORDER BY triggered_at DESC
        ''', (cutoff_date,))
        
        columns = [desc[0] for desc in cursor.description]
        alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tracked-urls', methods=['GET'])
def get_tracked_urls():
    """Obtiene las URLs que se están monitoreando"""
    try:
        urls = scraper.get_tracked_urls()
        return jsonify({
            'success': True,
            'data': urls,
            'count': len(urls)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tracked-urls', methods=['POST'])
def add_tracked_url():
    """Agrega una nueva URL para monitorear"""
    try:
        data = request.json
        url = data.get('url')
        category = data.get('category')
        description = data.get('description')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL es requerida'
            }), 400
        
        scraper.add_tracked_url(url, category, description)
        
        return jsonify({
            'success': True,
            'message': 'URL agregada exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/track-now', methods=['POST'])
def track_now():
    """Ejecuta el tracking inmediatamente"""
    try:
        scraper.run_tracking()
        return jsonify({
            'success': True,
            'message': 'Tracking ejecutado exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    """Hace scrape de una URL específica sin agregarla al tracking"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL es requerida'
            }), 400
        
        product = scraper.scrape_product(url)
        
        if product:
            return jsonify({
                'success': True,
                'data': {
                    'product_id': product.product_id,
                    'title': product.title,
                    'price': product.price,
                    'original_price': product.original_price,
                    'currency': product.currency,
                    'discount_percentage': product.discount_percentage,
                    'seller_name': product.seller_name,
                    'seller_reputation': product.seller_reputation,
                    'sales_count': product.sales_count,
                    'free_shipping': product.free_shipping,
                    'stock_available': product.stock_available,
                    'rating': product.rating,
                    'reviews_count': product.reviews_count,
                    'url': product.url,
                    'image_url': product.image_url
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo extraer información del producto'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtiene estadísticas generales"""
    try:
        conn = sqlite3.connect(scraper.db_path)
        cursor = conn.cursor()
        
        # Total de productos únicos
        cursor.execute('SELECT COUNT(DISTINCT product_id) FROM products')
        total_products = cursor.fetchone()[0]
        
        # Productos con descuento actualmente
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT product_id, MAX(id) as max_id
                FROM products
                GROUP BY product_id
            ) AS latest
            JOIN products ON products.id = latest.max_id
            WHERE products.discount_percentage > 0
        ''')
        with_discount = cursor.fetchone()[0]
        
        # Productos sin stock
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT product_id, MAX(id) as max_id
                FROM products
                GROUP BY product_id
            ) AS latest
            JOIN products ON products.id = latest.max_id
            WHERE products.stock_available = 0
        ''')
        out_of_stock = cursor.fetchone()[0]
        
        # Alertas en últimos 7 días
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM price_alerts WHERE triggered_at >= ?', (cutoff_date,))
        recent_alerts = cursor.fetchone()[0]
        
        # Precio promedio
        cursor.execute('''
            SELECT AVG(price) FROM (
                SELECT product_id, MAX(id) as max_id
                FROM products
                GROUP BY product_id
            ) AS latest
            JOIN products ON products.id = latest.max_id
        ''')
        avg_price = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'with_discount': with_discount,
                'out_of_stock': out_of_stock,
                'recent_alerts': recent_alerts,
                'average_price': round(avg_price, 2)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/price-comparison', methods=['GET'])
def price_comparison():
    """Compara precios de productos similares"""
    try:
        # Obtener productos con sus precios actuales
        products = scraper.get_all_products_latest()
        
        # Agrupar por categoría para comparación
        by_category = {}
        for product in products:
            category = product.get('category', 'Otros')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(product)
        
        # Calcular estadísticas por categoría
        comparison = {}
        for category, items in by_category.items():
            prices = [p['price'] for p in items]
            comparison[category] = {
                'count': len(items),
                'min_price': min(prices) if prices else 0,
                'max_price': max(prices) if prices else 0,
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'products': items
            }
        
        return jsonify({
            'success': True,
            'data': comparison
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Mercado Libre Tracker API Server")
    print("=" * 80)
    print("\n📍 Dashboard disponible en: http://localhost:5000")
    print("📡 API endpoints:")
    print("   GET  /api/products              - Lista todos los productos")
    print("   GET  /api/products/<id>/history - Historial de un producto")
    print("   GET  /api/alerts                - Alertas recientes")
    print("   GET  /api/tracked-urls          - URLs monitoreadas")
    print("   POST /api/tracked-urls          - Agregar URL")
    print("   POST /api/track-now             - Ejecutar tracking ahora")
    print("   POST /api/scrape-url            - Scrape una URL específica")
    print("   GET  /api/stats                 - Estadísticas generales")
    print("   GET  /api/price-comparison      - Comparación de precios")
    print("\n" + "=" * 80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
