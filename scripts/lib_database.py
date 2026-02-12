"""
DAIA - Database Module (SQLite Local)
Persistencia 100% local sin servidores externos.
100% Local, 0 USD, Control Total.
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DAIADatabase:
    """Gestor de base de datos SQLite para DAIA"""
    
    def __init__(self, db_path: str = "data/daia_audit.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta del archivo SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = None
        self._connect()
        self._create_tables()
        
        logger.info(f"✓ Database inicializada en {self.db_path}")
    
    def _connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = sqlite3.connect(str(self.db_path), timeout=10)
            self.connection.row_factory = sqlite3.Row  # Acceso por columna
            self.connection.execute("PRAGMA foreign_keys = ON")  # Validación de FK
            logger.info("✓ Conexión a SQLite establecida")
        except sqlite3.OperationalError as e:
            logger.error(f"❌ Error conectando a database: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado conectando: {e}")
            raise
    
    def _create_tables(self):
        """Crea tablas necesarias"""
        cursor = self.connection.cursor()
        
        # Tabla: CALLS (registro de llamadas procesadas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                original_filename TEXT,
                processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds REAL,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                service_level TEXT,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla: TRANSCRIPTS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                raw_text TEXT,
                cleaned_text TEXT,
                language TEXT,
                model_used TEXT,
                device_used TEXT,
                processing_time_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        # Tabla: QA_SCORES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                level TEXT,
                score REAL,
                max_score REAL,
                compliance_percentage REAL,
                classification TEXT,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        # Tabla: RISK_ASSESSMENTS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                risk_level TEXT,
                risk_score REAL,
                critical_keywords TEXT,
                warning_keywords TEXT,
                sentiment_factor REAL,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        # Tabla: KPI_RESULTS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpi_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                metric_unit TEXT,
                classification TEXT,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        # Tabla: SENTIMENT_ANALYSIS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                sentiment_overall TEXT,
                sentiment_score REAL,
                operator_sentiment TEXT,
                client_sentiment TEXT,
                segments JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        # Tabla: AUDIT_LOGS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER,
                level TEXT,
                message TEXT,
                error_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(call_id) REFERENCES calls(id)
            )
        """)
        
        self.connection.commit()
        logger.info("✓ Tablas creadas/verificadas")
    
    def insert_call(self, filename: str, duration: float = None, 
                   service_level: str = "standard", audio_path: str = None) -> int:
        """Inserta registro de nueva llamada con validaciones"""
        
        # Validar entrada
        if not filename or not isinstance(filename, str):
            logger.error(f"❌ Filename inválido: {filename}")
            return None
        
        if duration is not None and (not isinstance(duration, (int, float)) or duration < 0):
            logger.error(f"❌ Duration inválida: {duration}")
            return None
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO calls (filename, original_filename, duration_seconds, service_level)
                VALUES (?, ?, ?, ?)
            """, (filename, filename, duration, service_level))
            
            self.connection.commit()
            call_id = cursor.lastrowid
            
            logger.debug(f"✓ Llamada {call_id} registrada: {filename}")
            return call_id
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"⚠️ Llamada '{filename}' ya existe en BD")
            try:
                cursor.execute("SELECT id FROM calls WHERE filename = ?", (filename,))
                result = cursor.fetchone()
                return result[0] if result else None
            except Exception as e:
                logger.error(f"❌ Error recuperando ID existente: {e}")
                return None
        except sqlite3.DatabaseError as e:
            logger.error(f"❌ Error BD insertando llamada: {e}")
            return None
    
    def insert_transcript(self, call_id: int, text_raw: str = None, text_clean: str = None,
                         language: str = "es", model_used: str = "whisper",
                         device_used: str = "cpu", processing_time: float = 0, **kwargs):
        """Inserta transcripción con validaciones.

        Acepta aliases raw_text/cleaned_text para compatibilidad hacia atrás.
        """

        # Compatibilidad: permitir raw_text/cleaned_text
        if text_raw is None:
            text_raw = kwargs.get("raw_text")
        if text_clean is None:
            text_clean = kwargs.get("cleaned_text")

        # Validar entrada
        if not call_id or not isinstance(call_id, int):
            logger.error(f"❌ call_id inválido: {call_id}")
            return False
        
        if not text_raw or not isinstance(text_raw, str):
            logger.error("❌ text_raw inválido")
            return False
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO transcripts 
                (call_id, raw_text, cleaned_text, language, model_used, device_used, processing_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (call_id, text_raw, text_clean or text_raw, language, model_used, device_used, processing_time))
            
            self.connection.commit()
            logger.debug(f"✓ Transcripción guardada para llamada {call_id}")
            return True
            
        except sqlite3.DatabaseError as e:
            logger.error(f"❌ Error BD guardando transcripción: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado guardando transcripción: {e}")
            return False
    
    def insert_qa_score(self, call_id: int, qa_result: Dict = None, **kwargs):
        """Inserta resultado QA.

        Acepta el dict completo o kwargs (score, compliance_percentage, classification...).
        """
        data = qa_result or {}
        if kwargs:
            # Permitir compatibilidad con llamadas antiguas
            data = {
                'level': kwargs.get('level') or data.get('level'),
                'score': kwargs.get('score', data.get('score')),
                'max_score': kwargs.get('max_score', data.get('max_score')),
                'compliance_percentage': kwargs.get('compliance_percentage', data.get('compliance_percentage')),
                'classification': kwargs.get('classification', data.get('classification')),
                'details': kwargs.get('details', data.get('details', [])),
            }

        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO qa_scores 
            (call_id, level, score, max_score, compliance_percentage, classification, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            data.get('level'),
            data.get('score'),
            data.get('max_score'),
            data.get('compliance_percentage'),
            data.get('classification'),
            json.dumps(data.get('details', []))
        ))
        
        self.connection.commit()
        logger.debug(f"✓ QA Score insertada para call {call_id}")
    
    def insert_risk_assessment(self, call_id: int, risk_result: Dict = None, **kwargs):
        """Inserta análisis de riesgo.

        Soporta dict completo o kwargs (risk_level, risk_score, critical_keywords...).
        """
        data = risk_result or {}
        if kwargs:
            data = {
                'level': kwargs.get('risk_level', data.get('level')),
                'score': kwargs.get('risk_score', data.get('score', 0)),
                'critical_found': kwargs.get('critical_keywords', '').split(',') if isinstance(kwargs.get('critical_keywords'), str) else kwargs.get('critical_keywords', data.get('critical_found', [])),
                'warnings_found': kwargs.get('warnings', '').split(',') if isinstance(kwargs.get('warnings'), str) else kwargs.get('warnings', data.get('warnings_found', [])),
                'sentiment_factor': kwargs.get('sentiment_factor', data.get('sentiment_factor', 0)),
                'details': kwargs.get('details', data.get('details', {}))
            }

        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO risk_assessments 
            (call_id, risk_level, risk_score, critical_keywords, warning_keywords, sentiment_factor, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            data.get('level'),
            data.get('score', 0),
            ','.join(data.get('critical_found', [])),
            ','.join(data.get('warnings_found', [])),
            data.get('sentiment_factor', 0),
            json.dumps(data.get('details', risk_result or data))
        ))
        
        self.connection.commit()
        logger.debug(f"✓ Risk Assessment insertada para call {call_id}")
    
    def insert_kpi_metrics(self, call_id: int, kpis: Dict):
        """Inserta métricas KPI"""
        cursor = self.connection.cursor()
        
        for metric_name, metric_data in kpis.get('metrics', {}).items():
            cursor.execute("""
                INSERT INTO kpi_results 
                (call_id, metric_name, metric_value, metric_unit, classification, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                metric_name,
                metric_data.get('value', 0),
                metric_data.get('unit', ''),
                metric_data.get('classification', 'N/A'),
                json.dumps(metric_data)
            ))
        
        self.connection.commit()
        logger.debug(f"✓ KPI Metrics insertadas para call {call_id}")
    
    def insert_sentiment_analysis(self, call_id: int, sentiment_result: Dict = None, **kwargs):
        """Inserta análisis de sentimiento.

        Soporta dict completo o kwargs (hablante/sentiment/score, etc.).
        """
        data = sentiment_result or {}
        if kwargs:
            data = {
                'overall': kwargs.get('sentiment', data.get('overall')),
                'score': kwargs.get('score', data.get('score', 0)),
                'operator_sentiment': kwargs.get('operator_sentiment', data.get('operator_sentiment')), 
                'client_sentiment': kwargs.get('client_sentiment', data.get('client_sentiment')),
                'segments': kwargs.get('segments', data.get('segments', [])),
            }

        cursor = self.connection.cursor()
        
        # Extract nested values safely
        overall = data.get('overall', 'unknown')
        if isinstance(overall, dict):
            overall = overall.get('label') or overall.get('overall', 'unknown')
        
        score = data.get('score', 0)
        if isinstance(score, dict):
            score = score.get('score', 0)
        
        operator_sentiment = data.get('operator_sentiment', {})
        if isinstance(operator_sentiment, dict):
            operator_sentiment = operator_sentiment.get('label') or operator_sentiment.get('overall', 'unknown')
        
        client_sentiment = data.get('client_sentiment', {})
        if isinstance(client_sentiment, dict):
            client_sentiment = client_sentiment.get('label') or client_sentiment.get('overall', 'unknown')
        
        cursor.execute("""
            INSERT INTO sentiment_analysis 
            (call_id, sentiment_overall, sentiment_score, operator_sentiment, client_sentiment, segments)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            overall,
            score,
            operator_sentiment,
            client_sentiment,
            json.dumps(data.get('segments', []))
        ))
        
        self.connection.commit()
        logger.debug(f"✓ Sentiment Analysis insertada para call {call_id}")
    
    def insert_audit_log(self, call_id: int, level: str, message: str, error_type: str = None):
        """Inserta entrada en log de auditoría"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs (call_id, level, message, error_type)
            VALUES (?, ?, ?, ?)
        """, (call_id, level, message, error_type))
        
        self.connection.commit()
    
    def get_call(self, call_id: int) -> Optional[Dict]:
        """Obtiene datos de una llamada"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM calls WHERE id = ?", (call_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_call_analysis(self, call_id: int) -> Dict:
        """Obtiene análisis completo de una llamada"""
        result = {
            'call': self.get_call(call_id),
            'transcript': None,
            'qa_score': None,
            'risk_assessment': None,
            'sentiment': None,
            'kpis': None,
            'logs': None
        }
        
        cursor = self.connection.cursor()
        
        # Transcript
        cursor.execute("SELECT * FROM transcripts WHERE call_id = ? ORDER BY created_at DESC LIMIT 1",
                      (call_id,))
        row = cursor.fetchone()
        result['transcript'] = dict(row) if row else None
        
        # QA
        cursor.execute("SELECT * FROM qa_scores WHERE call_id = ? ORDER BY created_at DESC LIMIT 1",
                      (call_id,))
        row = cursor.fetchone()
        result['qa_score'] = dict(row) if row else None
        
        # Risk
        cursor.execute("SELECT * FROM risk_assessments WHERE call_id = ? ORDER BY created_at DESC LIMIT 1",
                      (call_id,))
        row = cursor.fetchone()
        result['risk_assessment'] = dict(row) if row else None
        
        # Sentiment
        cursor.execute("SELECT * FROM sentiment_analysis WHERE call_id = ? ORDER BY created_at DESC LIMIT 1",
                      (call_id,))
        row = cursor.fetchone()
        result['sentiment'] = dict(row) if row else None
        
        # KPIs
        cursor.execute("SELECT * FROM kpi_results WHERE call_id = ? ORDER BY created_at DESC",
                      (call_id,))
        rows = cursor.fetchall()
        result['kpis'] = [dict(row) for row in rows]
        
        # Logs
        cursor.execute("SELECT * FROM audit_logs WHERE call_id = ? ORDER BY timestamp DESC",
                      (call_id,))
        rows = cursor.fetchall()
        result['logs'] = [dict(row) for row in rows]
        
        return result
    
    def get_calls_summary(self, limit: int = 100) -> List[Dict]:
        """Obtiene resumen de últimas llamadas procesadas"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT 
                c.id, c.filename, c.status, c.service_level,
                q.compliance_percentage as qa_score,
                r.risk_level,
                s.sentiment_overall
            FROM calls c
            LEFT JOIN qa_scores q ON c.id = q.call_id
            LEFT JOIN risk_assessments r ON c.id = r.call_id
            LEFT JOIN sentiment_analysis s ON c.id = s.call_id
            ORDER BY c.created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def update_call_status(self, call_id: int, status: str, error_message: str = None):
        """Actualiza estado de una llamada"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            UPDATE calls SET status = ?, error_message = ?
            WHERE id = ?
        """, (status, error_message, call_id))
        
        self.connection.commit()
    
    def close(self):
        """Cierra conexión con la BD"""
        if self.connection:
            self.connection.close()
            logger.info("✓ Conexión a BD cerrada")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Usar con context manager
    with DAIADatabase("../data/daia_audit.db") as db:
        # Insertar llamada de prueba
        call_id = db.insert_call("test_call.wav", duration=180.5, service_level="standard")
        print(f"Call ID creada: {call_id}")
        
        # Insertar transcripción
        db.insert_transcript(
            call_id,
            raw_text="Buenos días...",
            cleaned_text="Buenos días...",
            language="es"
        )
        
        # Obtener análisis
        analysis = db.get_call_analysis(call_id)
        print(f"\nAnálisis de call {call_id}:")
        print(f"  Filename: {analysis['call']['filename']}")
        print(f"  Status: {analysis['call']['status']}")
