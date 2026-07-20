#!/usr/bin/env python3
"""
Automatización de tracking diario para Mercado Libre
Ejecuta scraping programado y envía notificaciones
"""

import schedule
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ml_scraper import MercadoLibreScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrackerScheduler:
    """Planificador de tareas para el tracker"""
    
    def __init__(self, db_path: str = "ml_tracker.db"):
        self.scraper = MercadoLibreScraper(db_path)
        self.email_config = None
    
    def configure_email(self, smtp_server: str, smtp_port: int, 
                       sender_email: str, sender_password: str, 
                       recipient_email: str):
        """Configura el envío de emails para notificaciones"""
        self.email_config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'recipient_email': recipient_email
        }
        logger.info("✓ Configuración de email establecida")
    
    def send_email_notification(self, subject: str, body: str):
        """Envía una notificación por email"""
        if not self.email_config:
            logger.warning("Email no configurado, saltando notificación")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                           self.email_config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"✓ Email enviado: {subject}")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def daily_tracking_job(self):
        """Job que se ejecuta diariamente"""
        logger.info("=" * 60)
        logger.info("🕐 INICIANDO TRACKING DIARIO")
        logger.info("=" * 60)
        
        try:
            # Ejecutar tracking
            self.scraper.run_tracking()
            
            # Recopilar alertas del día
            alerts = self.get_todays_alerts()
            
            # Generar reporte
            report = self.generate_daily_report(alerts)
            
            # Enviar notificación si hay alertas importantes
            if alerts:
                self.send_email_notification(
                    f"🔔 Mercado Libre Tracker - {len(alerts)} alertas",
                    report
                )
            
            logger.info("✓ Tracking diario completado exitosamente")
            
        except Exception as e:
            logger.error(f"Error en tracking diario: {e}")
            self.send_email_notification(
                "❌ Error en Mercado Libre Tracker",
                f"<p>Ocurrió un error durante el tracking:</p><pre>{str(e)}</pre>"
            )
    
    def get_todays_alerts(self):
        """Obtiene las alertas del día"""
        import sqlite3
        conn = sqlite3.connect(self.scraper.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT * FROM price_alerts 
            WHERE DATE(triggered_at) = ?
            ORDER BY triggered_at DESC
        ''', (today,))
        
        columns = [desc[0] for desc in cursor.description]
        alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return alerts
    
    def generate_daily_report(self, alerts):
        """Genera un reporte HTML con las alertas del día"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .alert { 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-radius: 5px;
                    border-left: 4px solid #f44336;
                }
                .price-drop { border-left-color: #4caf50; background-color: #e8f5e9; }
                .out-of-stock { border-left-color: #ff9800; background-color: #fff3e0; }
                h1 { color: #333; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>📊 Reporte Diario - Mercado Libre Tracker</h1>
            <div class="summary">
                <p><strong>Fecha:</strong> {date}</p>
                <p><strong>Total de alertas:</strong> {total_alerts}</p>
            </div>
        """.format(
            date=datetime.now().strftime('%d/%m/%Y %H:%M'),
            total_alerts=len(alerts)
        )
        
        if alerts:
            html += "<h2>🔔 Alertas del día:</h2>"
            for alert in alerts:
                alert_class = alert['alert_type'].replace('_', '-')
                html += f"""
                <div class="alert {alert_class}">
                    <strong>{alert['message']}</strong><br>
                    <small>{alert['triggered_at']}</small>
                </div>
                """
        else:
            html += "<p>No hay alertas para hoy.</p>"
        
        # Agregar resumen de productos
        products = self.scraper.get_all_products_latest()
        html += f"""
        <h2>📦 Resumen de productos monitoreados:</h2>
        <p>Total de productos: <strong>{len(products)}</strong></p>
        """
        
        html += "</body></html>"
        return html
    
    def schedule_jobs(self):
        """Configura los jobs programados"""
        # Tracking diario a las 9:00 AM
        schedule.every().day.at("09:00").do(self.daily_tracking_job)
        
        # Tracking adicional al mediodía (opcional)
        # schedule.every().day.at("12:00").do(self.daily_tracking_job)
        
        # Tracking en la tarde (opcional)
        # schedule.every().day.at("18:00").do(self.daily_tracking_job)
        
        logger.info("✓ Jobs programados:")
        logger.info("   - Tracking diario: 09:00 AM")
        logger.info("\n💡 Puedes agregar más horarios editando el archivo\n")
    
    def run(self):
        """Inicia el scheduler"""
        self.schedule_jobs()
        
        logger.info("=" * 60)
        logger.info("🚀 SCHEDULER INICIADO")
        logger.info("=" * 60)
        logger.info("\nPresiona Ctrl+C para detener\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            logger.info("\n👋 Scheduler detenido por el usuario")


def main():
    """Ejemplo de uso del scheduler"""
    scheduler = TrackerScheduler()
    
    # Configurar email (opcional)
    # scheduler.configure_email(
    #     smtp_server='smtp.gmail.com',
    #     smtp_port=587,
    #     sender_email='tu_email@gmail.com',
    #     sender_password='tu_contraseña_de_app',
    #     recipient_email='destinatario@email.com'
    # )
    
    # Iniciar el scheduler
    scheduler.run()


if __name__ == "__main__":
    main()
