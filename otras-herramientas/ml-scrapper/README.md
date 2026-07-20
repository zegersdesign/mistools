# 📊 Mercado Libre Tracker - Sistema de Seguimiento de Precios

Sistema completo de scraping, análisis y monitoreo de productos en Mercado Libre Chile con dashboard interactivo.

## 🚀 Características

✅ **Scraping automatizado** de productos de Mercado Libre Chile
✅ **Base de datos SQLite** para almacenar histórico de precios
✅ **Dashboard interactivo** con React y Chart.js
✅ **API REST** con Flask para consultas
✅ **Sistema de alertas** automáticas de descuentos y stock
✅ **Comparación de vendedores** y reputación
✅ **Gráficos de tendencias** de precios históricos
✅ **Automatización diaria** con scheduler
✅ **Notificaciones por email** (opcional)

---

## 📋 Requisitos

- Python 3.8+
- pip
- Navegador web moderno

---

## 🔧 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Verificar instalación

```bash
python ml_scraper.py --version
```

---

## 🎯 Uso Rápido

### Opción A: Usar el Dashboard Web (Recomendado)

1. **Iniciar el servidor:**

```bash
python ml_api.py
```

2. **Abrir en el navegador:**
   - URL: `http://localhost:5000`
   - El dashboard se abrirá automáticamente

3. **Agregar productos para monitorear:**
   - Desde el dashboard, usa el botón "Agregar Producto"
   - O usa la API POST `/api/tracked-urls`

### Opción B: Usar el Scraper Directamente

```python
from ml_scraper import MercadoLibreScraper

# Crear instancia del scraper
scraper = MercadoLibreScraper()

# Agregar URLs para monitorear
scraper.add_tracked_url(
    url='https://www.mercadolibre.cl/producto-ejemplo/p/MLC123456',
    category='Electrónica',
    description='Notebook HP'
)

# Ejecutar tracking
scraper.run_tracking()

# Ver productos
productos = scraper.get_all_products_latest()
for p in productos:
    print(f"{p['title']}: ${p['price']:,.0f}")
```

---

## 🤖 Automatización Diaria

Para ejecutar el scraping automáticamente todos los días:

```bash
python ml_scheduler.py
```

Por defecto, el tracking se ejecuta a las **9:00 AM** cada día.

### Personalizar horarios

Edita `ml_scheduler.py` y agrega más horarios:

```python
# En la función schedule_jobs()
schedule.every().day.at("09:00").do(self.daily_tracking_job)  # 9 AM
schedule.every().day.at("12:00").do(self.daily_tracking_job)  # 12 PM
schedule.every().day.at("18:00").do(self.daily_tracking_job)  # 6 PM
```

---

## 📧 Configurar Notificaciones por Email

### Para Gmail:

1. **Habilitar "Contraseñas de aplicaciones"** en tu cuenta de Google
2. **Editar `ml_scheduler.py`** en la función `main()`:

```python
scheduler.configure_email(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    sender_email='tu_email@gmail.com',
    sender_password='tu_contraseña_de_app',  # No tu contraseña normal
    recipient_email='destinatario@email.com'
)
```

---

## 🔌 API Endpoints

El servidor Flask expone los siguientes endpoints:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Dashboard web |
| GET | `/api/products` | Lista todos los productos |
| GET | `/api/products/<id>/history` | Historial de un producto |
| GET | `/api/alerts` | Alertas recientes |
| GET | `/api/tracked-urls` | URLs monitoreadas |
| POST | `/api/tracked-urls` | Agregar nueva URL |
| POST | `/api/track-now` | Ejecutar tracking ahora |
| POST | `/api/scrape-url` | Scrape una URL específica |
| GET | `/api/stats` | Estadísticas generales |
| GET | `/api/price-comparison` | Comparación de precios |

### Ejemplos de uso con curl:

```bash
# Obtener todos los productos
curl http://localhost:5000/api/products

# Agregar una URL para tracking
curl -X POST http://localhost:5000/api/tracked-urls \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.mercadolibre.cl/...", "category": "Electrónica"}'

# Ejecutar tracking inmediato
curl -X POST http://localhost:5000/api/track-now

# Scrape una URL sin agregarla al tracking
curl -X POST http://localhost:5000/api/scrape-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.mercadolibre.cl/..."}'
```

---

## 📊 Dashboard

El dashboard incluye:

- **Cards de estadísticas** (total productos, con descuento, sin stock, alertas)
- **Panel de alertas** con notificaciones de cambios importantes
- **Filtros** por categoría, descuentos, stock
- **Ordenamiento** por precio, descuento, rating
- **Tarjetas de productos** con toda la información
- **Modal de detalle** con gráfico de historial de precios
- **Análisis de tendencias** y recomendaciones

---

## 🗄️ Estructura de la Base de Datos

### Tabla `products`
Almacena cada snapshot de producto:
- `product_id`: ID del producto (MLC...)
- `title`: Título del producto
- `price`: Precio actual
- `original_price`: Precio antes del descuento
- `discount_percentage`: Porcentaje de descuento
- `seller_name`: Nombre del vendedor
- `seller_reputation`: Reputación (Platinum, Gold, etc)
- `sales_count`: Número de ventas
- `free_shipping`: Envío gratis (bool)
- `stock_available`: Stock disponible (bool)
- `rating`: Calificación (1-5)
- `reviews_count`: Número de reseñas
- `timestamp`: Fecha/hora del scraping

### Tabla `tracked_urls`
URLs a monitorear:
- `url`: URL del producto
- `category`: Categoría (Electrónica, etc)
- `description`: Descripción personalizada
- `active`: Si está activa (bool)

### Tabla `price_alerts`
Alertas generadas:
- `product_id`: ID del producto
- `alert_type`: Tipo (price_drop, out_of_stock)
- `threshold_value`: Valor del umbral
- `message`: Mensaje de la alerta
- `triggered_at`: Fecha/hora

---

## 💡 Ejemplos de Uso Avanzados

### 1. Monitorear múltiples productos

```python
from ml_scraper import MercadoLibreScraper

scraper = MercadoLibreScraper()

productos_a_monitorear = [
    {
        'url': 'https://www.mercadolibre.cl/notebook-...',
        'category': 'Electrónica',
        'description': 'Notebook trabajo'
    },
    {
        'url': 'https://www.mercadolibre.cl/celular-...',
        'category': 'Electrónica',
        'description': 'Samsung nuevo'
    },
    {
        'url': 'https://www.mercadolibre.cl/refrigerador-...',
        'category': 'Electrodomésticos',
        'description': 'Refri cocina'
    }
]

for producto in productos_a_monitorear:
    scraper.add_tracked_url(**producto)

scraper.run_tracking()
```

### 2. Análisis de historial de precios

```python
# Obtener historial de un producto
historial = scraper.get_price_history('MLC123456')

# Calcular precio promedio
precios = [h['price'] for h in historial]
precio_promedio = sum(precios) / len(precios)

# Encontrar precio mínimo y máximo
precio_min = min(precios)
precio_max = max(precios)

print(f"Precio actual: ${precios[-1]:,.0f}")
print(f"Precio promedio: ${precio_promedio:,.0f}")
print(f"Precio mínimo: ${precio_min:,.0f}")
print(f"Precio máximo: ${precio_max:,.0f}")

# Calcular tendencia
if precios[-1] < precio_promedio:
    print("💚 Buen momento para comprar (bajo promedio)")
else:
    print("⏳ Esperar, precio alto")
```

### 3. Comparar vendedores

```python
import sqlite3

conn = sqlite3.connect('ml_tracker.db')
cursor = conn.cursor()

# Obtener todos los vendedores de un producto específico
cursor.execute('''
    SELECT DISTINCT seller_name, seller_reputation, 
           AVG(price) as avg_price, 
           COUNT(*) as samples
    FROM products
    WHERE product_id = 'MLC123456'
    GROUP BY seller_name
    ORDER BY avg_price ASC
''')

print("Comparación de vendedores:")
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]}): ${row[2]:,.0f} promedio ({row[3]} muestras)")
```

---

## 🛠️ Troubleshooting

### Error: "No module named 'requests'"
```bash
pip install -r requirements.txt
```

### Error: "Permission denied" al ejecutar
```bash
chmod +x ml_scraper.py ml_api.py ml_scheduler.py
```

### El scraper no encuentra productos
- Verifica que la URL sea correcta
- Mercado Libre puede cambiar su estructura HTML
- Revisa los logs en `ml_tracker.log`

### Base de datos bloqueada
- Cierra otros procesos que usen la BD
- Reinicia el servidor

---

## 📝 Buenas Prácticas

1. **Respetar robots.txt**: Agregar delays entre requests
2. **No abusar del scraping**: Usar con moderación
3. **Mantener actualizado**: Revisar cambios en la estructura HTML
4. **Backup regular**: Respaldar la base de datos periódicamente
5. **Rotación de User-Agents**: Para mayor confiabilidad

---

## 🔐 Consideraciones de Seguridad

- **No compartir** tu base de datos con información personal
- **Encriptar contraseñas** de email si las usas
- **No versionar** archivos con credenciales
- Usar **variables de entorno** para información sensible

---

## 📈 Roadmap Futuro

- [ ] Integración con Telegram bot
- [ ] Predicción de precios con ML
- [ ] Comparación con otras tiendas
- [ ] Sistema de recomendaciones
- [ ] App móvil
- [ ] Exportar reportes a Excel/PDF
- [ ] Integración con Google Sheets

---

## 🤝 Contribuciones

Este es un proyecto educativo. Siéntete libre de:
- Reportar bugs
- Sugerir mejoras
- Agregar funcionalidades
- Mejorar la documentación

---

## ⚖️ Disclaimer Legal

Este proyecto es solo para fines educativos y de investigación personal. 

- ✅ Úsalo para tu propio beneficio como consumidor
- ❌ No lo uses con fines comerciales
- ❌ No sobrecargues los servidores de Mercado Libre
- ⚠️ Respeta los términos de servicio del sitio

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisa esta documentación
2. Busca en los logs (`ml_tracker.log`)
3. Verifica los issues conocidos

---

## 📄 Licencia

MIT License - Libre para uso personal y educativo

---

**¡Feliz tracking! 🎉**
