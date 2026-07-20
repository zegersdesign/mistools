#!/usr/bin/env python3
"""
Script de inicio rápido para Mercado Libre Tracker
Configura productos de ejemplo y ejecuta un primer tracking
"""

from ml_scraper import MercadoLibreScraper
import sys

def setup_example_products():
    """Configura productos de ejemplo para empezar"""
    
    print("=" * 70)
    print("🚀 CONFIGURACIÓN INICIAL - MERCADO LIBRE TRACKER")
    print("=" * 70)
    print()
    
    scraper = MercadoLibreScraper()
    
    # URLs de ejemplo - REEMPLAZAR CON TUS PRODUCTOS
    ejemplo_urls = {
        'Electrónica': [
            # Ejemplo: 'https://www.mercadolibre.cl/notebook-hp-156-intel-core-i5-8gb-ram-256gb-ssd/p/MLC123456',
            # Agrega tus URLs aquí
        ],
        'Electrodomésticos': [
            # Ejemplo: 'https://www.mercadolibre.cl/refrigerador-samsung-french-door/p/MLC789012',
            # Agrega tus URLs aquí
        ]
    }
    
    print("📝 Ingresa las URLs de productos que quieres monitorear")
    print("   (Presiona Enter sin texto para terminar)\n")
    
    categoria_actual = 'Electrónica'
    urls_agregadas = 0
    
    while True:
        print(f"\n📂 Categoría: {categoria_actual}")
        print("   Opciones: [1] Electrónica, [2] Electrodomésticos, [3] Otra, [Enter] Siguiente")
        
        categoria_input = input("Selecciona categoría (o Enter para continuar): ").strip()
        
        if categoria_input == '1':
            categoria_actual = 'Electrónica'
        elif categoria_input == '2':
            categoria_actual = 'Electrodomésticos'
        elif categoria_input == '3':
            categoria_actual = input("Nombre de categoría: ").strip() or 'Otros'
        elif categoria_input == '':
            # Pedir URL
            url = input("URL del producto (o Enter para terminar): ").strip()
            
            if not url:
                break
            
            if 'mercadolibre.cl' not in url:
                print("❌ URL inválida. Debe ser de mercadolibre.cl")
                continue
            
            descripcion = input("Descripción (opcional): ").strip()
            
            try:
                scraper.add_tracked_url(url, categoria_actual, descripcion)
                urls_agregadas += 1
                print(f"✅ Producto agregado ({urls_agregadas} total)")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    if urls_agregadas == 0:
        print("\n⚠️  No se agregaron productos. Saliendo...")
        return False
    
    print(f"\n✅ Total de productos agregados: {urls_agregadas}")
    print("\n¿Deseas ejecutar el primer tracking ahora? (s/n): ", end='')
    
    if input().lower() == 's':
        print("\n🔄 Ejecutando primer tracking...")
        print("   (Esto puede tomar unos minutos...)\n")
        scraper.run_tracking()
        
        # Mostrar resumen
        productos = scraper.get_all_products_latest()
        
        print("\n" + "=" * 70)
        print("📊 RESUMEN DEL TRACKING")
        print("=" * 70)
        
        for p in productos:
            print(f"\n✓ {p['title'][:60]}")
            print(f"  💰 ${p['price']:,.0f} {p['currency']}")
            if p['discount_percentage']:
                print(f"  🎯 Descuento: {p['discount_percentage']:.0f}%")
            print(f"  👤 Vendedor: {p['seller_name']}")
            print(f"  📦 Stock: {'Disponible' if p['stock_available'] else 'Agotado'}")
    
    print("\n" + "=" * 70)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("=" * 70)
    print("\n📌 Próximos pasos:")
    print("   1. Iniciar el servidor web: python ml_api.py")
    print("   2. Abrir dashboard: http://localhost:5000")
    print("   3. Automatizar tracking: python ml_scheduler.py")
    print()
    
    return True


def quick_test():
    """Test rápido de una URL"""
    print("\n🧪 TEST RÁPIDO - Probar una URL")
    print("=" * 70)
    
    url = input("\nURL del producto de Mercado Libre: ").strip()
    
    if not url or 'mercadolibre.cl' not in url:
        print("❌ URL inválida")
        return
    
    print("\n🔍 Scrapeando producto...\n")
    
    scraper = MercadoLibreScraper()
    producto = scraper.scrape_product(url)
    
    if producto:
        print("✅ Producto extraído exitosamente:\n")
        print(f"📦 Título: {producto.title}")
        print(f"💰 Precio: ${producto.price:,.0f} {producto.currency}")
        if producto.original_price:
            print(f"💵 Precio original: ${producto.original_price:,.0f}")
            print(f"🎯 Descuento: {producto.discount_percentage:.0f}%")
        print(f"👤 Vendedor: {producto.seller_name}")
        if producto.seller_reputation:
            print(f"⭐ Reputación: {producto.seller_reputation}")
        if producto.sales_count:
            print(f"📊 Ventas: {producto.sales_count}")
        print(f"📦 Stock: {'✓ Disponible' if producto.stock_available else '✗ Agotado'}")
        print(f"🚚 Envío gratis: {'✓ Sí' if producto.free_shipping else '✗ No'}")
        if producto.rating:
            print(f"⭐ Rating: {producto.rating}/5 ({producto.reviews_count} reseñas)")
        
        print("\n¿Agregar este producto al tracking? (s/n): ", end='')
        if input().lower() == 's':
            categoria = input("Categoría (Enter = Electrónica): ").strip() or 'Electrónica'
            descripcion = input("Descripción (opcional): ").strip()
            scraper.add_tracked_url(url, categoria, descripcion)
            scraper.save_product(producto)
            print("✅ Producto agregado al tracking")
    else:
        print("❌ No se pudo extraer el producto")


def main():
    """Menú principal"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MERCADO LIBRE TRACKER - INICIO RÁPIDO" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("1. Configuración inicial (agregar productos)")
    print("2. Test rápido (probar una URL)")
    print("3. Ver productos monitoreados")
    print("4. Salir")
    print()
    
    opcion = input("Selecciona una opción: ").strip()
    
    if opcion == '1':
        setup_example_products()
    elif opcion == '2':
        quick_test()
    elif opcion == '3':
        scraper = MercadoLibreScraper()
        urls = scraper.get_tracked_urls()
        if urls:
            print(f"\n📋 Productos monitoreados ({len(urls)}):\n")
            for i, url in enumerate(urls, 1):
                print(f"{i}. [{url['category']}] {url['description'] or 'Sin descripción'}")
                print(f"   {url['url'][:80]}...")
                print(f"   Estado: {'✓ Activo' if url['active'] else '✗ Inactivo'}\n")
        else:
            print("\n⚠️  No hay productos monitoreados todavía")
            print("   Usa la opción 1 para agregar productos\n")
    elif opcion == '4':
        print("\n👋 ¡Hasta luego!\n")
        sys.exit(0)
    else:
        print("\n❌ Opción inválida\n")
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Proceso cancelado por el usuario\n")
        sys.exit(0)
