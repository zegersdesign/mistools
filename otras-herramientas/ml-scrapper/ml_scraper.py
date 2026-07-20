#!/usr/bin/env python3
"""
Mercado Libre Chile - Price Tracker & Scraper
Monitorea precios, stock y vendedores de productos en Mercado Libre Chile
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
from datetime import datetime
import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Estructura de datos para un producto"""
    product_id: str
    title: str
    price: float
    original_price: Optional[float]
    currency: str
    discount_percentage: Optional[float]
    seller_name: str
    seller_reputation: Optional[str]
    sales_count: Optional[int]
    free_shipping: bool
    stock_available: bool
    rating: Optional[float]
    reviews_count: Optional[int]
    url: str
    image_url: Optional[str]
    timestamp: str


class MercadoLibreScraper:
    """Scraper para Mercado Libre Chile"""
    
    BASE_URL = "https://www.mercadolibre.cl"
    
    def __init__(self, db_path: str = "ml_tracker.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'es-CL,es;q=0.9',
        })
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                original_price REAL,
                currency TEXT NOT NULL,
                discount_percentage REAL,
                seller_name TEXT,
                seller_reputation TEXT,
                sales_count INTEGER,
                free_shipping BOOLEAN,
                stock_available BOOLEAN,
                rating REAL,
                reviews_count INTEGER,
                url TEXT NOT NULL,
                image_url TEXT,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de URLs a monitorear
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracked_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                category TEXT,
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                threshold_value REAL,
                message TEXT,
                triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON products(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON products(timestamp)')
        
        conn.commit()
        conn.close()
        logger.info(f"Base de datos inicializada: {self.db_path}")
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extrae el ID del producto de la URL"""
        # MLC1234567890 format
        match = re.search(r'MLC\d+', url)
        return match.group(0) if match else None
    
    def scrape_product(self, url: str) -> Optional[Product]:
        """Scrape información de un producto individual"""
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_id = self.extract_product_id(url)
            
            if not product_id:
                logger.warning(f"No se pudo extraer ID del producto de: {url}")
                return None
            
            # Extraer datos del producto
            product_data = self._parse_product_page(soup, product_id, url)
            
            if product_data:
                logger.info(f"✓ Producto extraído: {product_data.title[:50]}...")
                return product_data
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error al hacer request: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return None
    
    def _parse_product_page(self, soup: BeautifulSoup, product_id: str, url: str) -> Optional[Product]:
        """Parsea la página del producto"""
        try:
            # Título
            title_elem = soup.find('h1', class_='ui-pdp-title')
            title = title_elem.text.strip() if title_elem else "Sin título"
            
            # Precio actual
            price_elem = soup.find('span', class_='andes-money-amount__fraction')
            price = float(price_elem.text.strip().replace('.', '').replace(',', '.')) if price_elem else 0.0
            
            # Moneda
            currency_elem = soup.find('span', class_='andes-money-amount__currency-symbol')
            currency = currency_elem.text.strip() if currency_elem else 'CLP'
            
            # Precio original (si hay descuento)
            original_price_elem = soup.find('s', class_='andes-money-amount--previous')
            original_price = None
            if original_price_elem:
                price_text = original_price_elem.find('span', class_='andes-money-amount__fraction')
                if price_text:
                    original_price = float(price_text.text.strip().replace('.', '').replace(',', '.'))
            
            # Descuento
            discount_elem = soup.find('span', class_='andes-money-amount__discount')
            discount_percentage = None
            if discount_elem:
                discount_text = discount_elem.text.strip().replace('%', '').replace('OFF', '').strip()
                discount_percentage = float(discount_text) if discount_text else None
            
            # Vendedor
            seller_elem = soup.find('div', class_='ui-pdp-seller__header__title')
            seller_name = seller_elem.text.strip() if seller_elem else "Desconocido"
            
            # Reputación del vendedor
            reputation_elem = soup.find('p', class_='ui-pdp-seller__status-title')
            seller_reputation = reputation_elem.text.strip() if reputation_elem else None
            
            # Ventas
            sales_elem = soup.find('span', class_='ui-pdp-subtitle')
            sales_count = None
            if sales_elem and 'vendidos' in sales_elem.text.lower():
                sales_text = re.search(r'(\d+)', sales_elem.text.replace('.', ''))
                sales_count = int(sales_text.group(1)) if sales_text else None
            
            # Envío gratis
            shipping_elem = soup.find('p', class_='ui-pdp-color--GREEN')
            free_shipping = shipping_elem and 'gratis' in shipping_elem.text.lower()
            
            # Stock disponible
            stock_elem = soup.find('span', class_='ui-pdp-buybox__quantity__available')
            stock_available = not (soup.find(text=re.compile(r'no disponible|sin stock', re.I)))
            
            # Rating y reseñas
            rating_elem = soup.find('p', class_='ui-pdp-review__rating')
            rating = float(rating_elem.text.strip()) if rating_elem else None
            
            reviews_elem = soup.find('span', class_='ui-pdp-review__amount')
            reviews_count = None
            if reviews_elem:
                reviews_text = re.search(r'(\d+)', reviews_elem.text.replace('.', ''))
                reviews_count = int(reviews_text.group(1)) if reviews_text else None
            
            # Imagen
            image_elem = soup.find('img', class_='ui-pdp-image')
            image_url = image_elem.get('src') if image_elem else None
            
            return Product(
                product_id=product_id,
                title=title,
                price=price,
                original_price=original_price,
                currency=currency,
                discount_percentage=discount_percentage,
                seller_name=seller_name,
                seller_reputation=seller_reputation,
                sales_count=sales_count,
                free_shipping=free_shipping,
                stock_available=stock_available,
                rating=rating,
                reviews_count=reviews_count,
                url=url,
                image_url=image_url,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error al parsear producto: {e}")
            return None
    
    def save_product(self, product: Product):
        """Guarda el producto en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        product_dict = asdict(product)
        columns = ', '.join(product_dict.keys())
        placeholders = ', '.join(['?'] * len(product_dict))
        
        cursor.execute(
            f'INSERT INTO products ({columns}) VALUES ({placeholders})',
            list(product_dict.values())
        )
        
        conn.commit()
        conn.close()
        logger.info(f"✓ Producto guardado: {product.product_id}")
    
    def add_tracked_url(self, url: str, category: str = None, description: str = None):
        """Agrega una URL para monitorear"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO tracked_urls (url, category, description) VALUES (?, ?, ?)',
                (url, category, description)
            )
            conn.commit()
            logger.info(f"✓ URL agregada para tracking: {url}")
        except sqlite3.IntegrityError:
            logger.warning(f"URL ya existe en tracking: {url}")
        finally:
            conn.close()
    
    def get_tracked_urls(self) -> List[Dict]:
        """Obtiene todas las URLs activas a monitorear"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tracked_urls WHERE active = 1')
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def run_tracking(self):
        """Ejecuta el tracking de todos los productos activos"""
        logger.info("=== Iniciando tracking de productos ===")
        tracked_urls = self.get_tracked_urls()
        
        if not tracked_urls:
            logger.warning("No hay URLs para trackear. Usa add_tracked_url() primero.")
            return
        
        for item in tracked_urls:
            url = item['url']
            product = self.scrape_product(url)
            
            if product:
                self.save_product(product)
                self.check_alerts(product)
            
            # Delay entre requests para ser respetuosos
            time.sleep(2)
        
        logger.info("=== Tracking completado ===")
    
    def check_alerts(self, product: Product):
        """Verifica si se debe generar una alerta para el producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener historial del producto
        cursor.execute(
            'SELECT price FROM products WHERE product_id = ? ORDER BY timestamp DESC LIMIT 5',
            (product.product_id,)
        )
        prices = [row[0] for row in cursor.fetchall()]
        
        # Alerta de descuento significativo (>20%)
        if len(prices) > 1:
            price_drop = ((prices[1] - prices[0]) / prices[1]) * 100
            if price_drop > 20:
                message = f"¡Alerta! {product.title} bajó {price_drop:.1f}% (${prices[1]:,.0f} → ${prices[0]:,.0f})"
                cursor.execute(
                    'INSERT INTO price_alerts (product_id, alert_type, threshold_value, message) VALUES (?, ?, ?, ?)',
                    (product.product_id, 'price_drop', price_drop, message)
                )
                logger.warning(f"🚨 {message}")
        
        # Alerta de stock bajo
        if not product.stock_available:
            message = f"⚠️ {product.title} SIN STOCK"
            cursor.execute(
                'INSERT INTO price_alerts (product_id, alert_type, threshold_value, message) VALUES (?, ?, ?, ?)',
                (product.product_id, 'out_of_stock', 0, message)
            )
            logger.warning(message)
        
        conn.commit()
        conn.close()
    
    def get_price_history(self, product_id: str) -> List[Dict]:
        """Obtiene el historial de precios de un producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT timestamp, price, discount_percentage, seller_name, stock_available 
               FROM products 
               WHERE product_id = ? 
               ORDER BY timestamp ASC''',
            (product_id,)
        )
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_all_products_latest(self) -> List[Dict]:
        """Obtiene el último registro de cada producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products 
            WHERE id IN (
                SELECT MAX(id) 
                FROM products 
                GROUP BY product_id
            )
            ORDER BY timestamp DESC
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results


def main():
    """Ejemplo de uso"""
    scraper = MercadoLibreScraper()
    
    # URLs de ejemplo (reemplazar con URLs reales)
    example_urls = [
        # "https://www.mercadolibre.cl/notebook-example/p/MLC123456",
        # "https://www.mercadolibre.cl/celular-example/p/MLC789012",
    ]
    
    # Agregar URLs para tracking
    for url in example_urls:
        scraper.add_tracked_url(url, category="Electrónica", description="Producto de ejemplo")
    
    # Ejecutar tracking
    scraper.run_tracking()
    
    print("\n📊 Dashboard de productos:")
    print("-" * 80)
    products = scraper.get_all_products_latest()
    for product in products:
        print(f"\n{product['title'][:60]}")
        print(f"  💰 Precio: ${product['price']:,.0f} {product['currency']}")
        if product['discount_percentage']:
            print(f"  🎯 Descuento: {product['discount_percentage']:.0f}%")
        print(f"  📦 Stock: {'✓' if product['stock_available'] else '✗'}")
        print(f"  🚚 Envío gratis: {'✓' if product['free_shipping'] else '✗'}")
        if product['rating']:
            print(f"  ⭐ Rating: {product['rating']}/5 ({product['reviews_count']} reseñas)")


if __name__ == "__main__":
    main()
