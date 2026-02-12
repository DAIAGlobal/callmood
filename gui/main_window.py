"""
DAIA 2.0 - GUI Principal
Interfaz gráfica para procesamiento de audios
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QComboBox,
    QGroupBox, QProgressBar, QMessageBox, QLineEdit, QListWidget,
    QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

# Habilitar import de scripts (rules_engine)
ROOT_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from scripts.rules_engine import RuleSetRepository, RuleEngine, RuleSet
from gui.formatters import format_percentage, format_seconds, format_words


class ProcessThread(QThread):
    """Thread para procesar archivo individual"""

    output_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, audio_file, service_level="standard", rules_user="default"):
        super().__init__()
        self.audio_file = audio_file
        self.service_level = service_level
        self.process = None
        self.rules_user = rules_user

    def run(self):
        try:
            root_dir = Path(__file__).parent.parent
            script_path = root_dir / "process_audios.py"
            python_exe = sys.executable

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
            env["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "1"
            env["DAIA_RULES_USER"] = self.rules_user

            self.process = subprocess.Popen(
                [python_exe, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(root_dir),
                env=env,
            )

            self.process.stdin.write("1\n")
            self.process.stdin.flush()
            self.process.stdin.write(f"{self.audio_file}\n")
            self.process.stdin.flush()
            self.process.stdin.write(f"{self.service_level}\n")
            self.process.stdin.flush()
            self.process.stdin.write("4\n")
            self.process.stdin.flush()
            self.process.stdin.close()

            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.output_signal.emit(line.rstrip())

            self.process.wait()
            if self.process.returncode == 0:
                self.finished_signal.emit(True, "Procesamiento completado")
            else:
                self.finished_signal.emit(False, f"Error en procesamiento (código: {self.process.returncode})")

        except Exception as exc:
            self.output_signal.emit(f"ERROR: {exc}")
            self.finished_signal.emit(False, str(exc))


class BatchProcessThread(QThread):
    """Thread para procesar carpeta completa"""

    output_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, audio_folder, rules_user="default"):
        super().__init__()
        self.audio_folder = audio_folder
        self.process = None
        self.rules_user = rules_user

    def run(self):
        try:
            root_dir = Path(__file__).parent.parent
            script_path = root_dir / "process_audios.py"
            python_exe = sys.executable

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
            env["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "1"
            env["DAIA_RULES_USER"] = self.rules_user

            self.process = subprocess.Popen(
                [python_exe, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(root_dir),
                env=env,
            )

            self.process.stdin.write("2\n")
            self.process.stdin.flush()
            self.process.stdin.write("4\n")
            self.process.stdin.flush()
            self.process.stdin.close()

            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.output_signal.emit(line.rstrip())

            self.process.wait()
            if self.process.returncode == 0:
                self.finished_signal.emit(True, "Procesamiento en lote completado")
            else:
                self.finished_signal.emit(False, f"Error en procesamiento (código: {self.process.returncode})")

        except Exception as exc:
            self.output_signal.emit(f"ERROR: {exc}")
            self.finished_signal.emit(False, str(exc))


class DAIAMainWindow(QMainWindow):
    """Ventana principal de la aplicación GUI"""
    
    def __init__(self):
        super().__init__()
        self.process_thread = None
        self.rules_repo = RuleSetRepository(ROOT_DIR / "data" / "rulesets.json")
        self.rules_engine = RuleEngine(self.rules_repo)
        self.current_user_id = "default"
        self.dark_mode = False
        self.init_ui()
        self.check_directories()
        
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("DAIA 2.0 - Sistema de Auditoría de Llamadas")
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        self.create_header(main_layout)

        # Tabs principales
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tabs)

        # Construir tabs
        self.tabs.addTab(self.build_process_tab(), "Procesar")
        self.tabs.addTab(self.build_rules_tab(), "Reglas")
        self.tabs.addTab(self.build_reports_tab(), "Reportes")
        self.tabs.addTab(self.build_config_tab(), "Config")

        # Barra de estado
        self.statusBar().showMessage("Listo")
        
        # Aplicar estilos
        self.apply_styles()
        self.apply_widget_theme()
        
    def create_header(self, layout):
        """Crear header de la aplicación"""
        header_group = QGroupBox()
        header_layout = QVBoxLayout()
        
        title = QLabel("DAIA 2.0")
        title.setFont(QFont("Manrope", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Sistema de Auditoría y Compliance - 100% Local")
        subtitle.setFont(QFont("Manrope", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
    def build_process_tab(self):
        """Tab: procesamiento y logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        control_group = QGroupBox("Panel de Control")
        control_layout = QVBoxLayout()
        
        # Selector de archivo
        file_layout = QHBoxLayout()
        file_label = QLabel("Archivo de audio:")
        file_label.setMinimumWidth(120)
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Selecciona un archivo de audio...")
        self.file_browse_btn = QPushButton("📁 Explorar")
        self.file_browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.file_browse_btn)
        control_layout.addLayout(file_layout)
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Carpeta de audios:")
        folder_label.setMinimumWidth(120)
        self.folder_path_input = QLineEdit()
        default_folder = Path(__file__).parent.parent / "audio_in"
        self.folder_path_input.setText(str(default_folder))
        self.folder_browse_btn = QPushButton("📁 Explorar")
        self.folder_browse_btn.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_path_input)
        folder_layout.addWidget(self.folder_browse_btn)
        control_layout.addLayout(folder_layout)
        
        # Selector de nivel de análisis
        level_layout = QHBoxLayout()
        level_label = QLabel("Nivel de análisis:")
        level_label.setMinimumWidth(120)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["basic", "standard", "advanced"])
        self.level_combo.setCurrentText("standard")
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        control_layout.addLayout(level_layout)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.process_file_btn = QPushButton("🎙️ Procesar Archivo Individual")
        self.process_file_btn.setMinimumHeight(40)
        self.process_file_btn.clicked.connect(self.process_single_file)
        
        self.process_batch_btn = QPushButton("📊 Procesar Carpeta Completa")
        self.process_batch_btn.setMinimumHeight(40)
        self.process_batch_btn.clicked.connect(self.process_batch)
        
        self.stop_btn = QPushButton("⛔ Detener")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_process)
        
        buttons_layout.addWidget(self.process_file_btn)
        buttons_layout.addWidget(self.process_batch_btn)
        buttons_layout.addWidget(self.stop_btn)
        control_layout.addLayout(buttons_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Panel de logs dentro del tab
        self.create_log_panel(layout)
        return tab

    def build_config_tab(self):
        """Tab: accesos rápidos y rutas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        paths_group = QGroupBox("Accesos rápidos")
        paths_layout = QVBoxLayout()

        btn_audio = QPushButton("📂 Abrir audio_in")
        btn_audio.clicked.connect(lambda: os.startfile(str(Path(ROOT_DIR / "audio_in"))))
        btn_reports = QPushButton("📂 Abrir reports")
        btn_reports.clicked.connect(lambda: os.startfile(str(Path(ROOT_DIR / "reports"))))
        btn_rules = QPushButton("📄 Abrir data/rulesets.json")
        btn_rules.clicked.connect(lambda: os.startfile(str(Path(ROOT_DIR / "data" / "rulesets.json"))))

        toggle_theme_btn = QPushButton("🌙 Modo oscuro")
        toggle_theme_btn.clicked.connect(self.toggle_theme)

        paths_layout.addWidget(btn_audio)
        paths_layout.addWidget(btn_reports)
        paths_layout.addWidget(btn_rules)
        paths_layout.addWidget(toggle_theme_btn)
        paths_layout.addStretch()
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        return tab

    def build_rules_tab(self):
        """Tab: reglas por usuario con editor y prueba"""
        tab = QWidget()
        rules_layout = QVBoxLayout(tab)

        rules_group = QGroupBox("Chat de reglas (por usuario)")
        group_layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Usuario
        user_label = QLabel("Usuario (id):")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("ej: agente01")
        self.user_input.setText("default")
        self.user_input.textChanged.connect(self.on_user_changed)
        left_layout.addWidget(user_label)
        left_layout.addWidget(self.user_input)

        # Nombre de ruleset
        name_label = QLabel("Nombre del preset:")
        self.ruleset_name_input = QLineEdit()
        self.ruleset_name_input.setPlaceholderText("ej: Script ventas v1")
        left_layout.addWidget(name_label)
        left_layout.addWidget(self.ruleset_name_input)

        # Keywords y frases
        keywords_label = QLabel("Keywords (coma separadas):")
        self.keywords_input = QLineEdit()
        left_layout.addWidget(keywords_label)
        left_layout.addWidget(self.keywords_input)

        required_label = QLabel("Frases obligatorias (coma separadas):")
        self.required_input = QLineEdit()
        left_layout.addWidget(required_label)
        left_layout.addWidget(self.required_input)

        # Speech base
        speech_label = QLabel("Speech base / script:")
        self.speech_input = QTextEdit()
        self.speech_input.setMinimumHeight(120)
        self.speech_input.setPlaceholderText("Pega aquí el guion base que debe cumplir el agente")
        right_layout.addWidget(speech_label)
        right_layout.addWidget(self.speech_input)

        form_layout.addLayout(left_layout)
        form_layout.addLayout(right_layout)

        # Botones guardar/activar
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Guardar y activar")
        save_btn.clicked.connect(self.save_ruleset_from_gui)
        refresh_btn = QPushButton("🔄 Recargar activo")
        refresh_btn.clicked.connect(self.refresh_ruleset_info)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addStretch()

        # Información del ruleset activo
        self.ruleset_info = QTextEdit()
        self.ruleset_info.setReadOnly(True)
        self.ruleset_info.setMinimumHeight(160)
        self.ruleset_info.setFont(QFont("Consolas", 9))

        group_layout.addLayout(form_layout)
        group_layout.addLayout(buttons_layout)
        group_layout.addWidget(self.ruleset_info)
        rules_group.setLayout(group_layout)
        rules_layout.addWidget(rules_group)

        # Probar texto con reglas
        test_group = QGroupBox("Probar reglas con texto de ejemplo")
        test_layout = QVBoxLayout()
        self.sample_text_input = QTextEdit()
        self.sample_text_input.setPlaceholderText("Pega un fragmento de transcripción para probar las reglas")
        self.sample_text_input.setMinimumHeight(120)
        test_buttons = QHBoxLayout()
        run_test_btn = QPushButton("▶ Probar texto")
        run_test_btn.clicked.connect(self.run_sample_rules_test)
        test_buttons.addWidget(run_test_btn)
        test_buttons.addStretch()
        self.sample_test_output = QTextEdit()
        self.sample_test_output.setReadOnly(True)
        self.sample_test_output.setMinimumHeight(120)
        self.sample_test_output.setFont(QFont("Consolas", 9))
        test_layout.addWidget(self.sample_text_input)
        test_layout.addLayout(test_buttons)
        test_layout.addWidget(self.sample_test_output)
        test_group.setLayout(test_layout)
        rules_layout.addWidget(test_group)

        self.refresh_ruleset_info()
        return tab
        
    def create_log_panel(self, layout):
        """Crear panel de logs"""
        log_group = QGroupBox("Logs de Procesamiento")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # Botones de control de logs
        log_buttons = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Limpiar Logs")
        clear_btn.clicked.connect(self.clear_logs)
        log_buttons.addStretch()
        log_buttons.addWidget(clear_btn)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_buttons)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
    def build_reports_tab(self):
        """Tab: reportes y detalles"""
        tab = QWidget()
        reports_layout = QVBoxLayout(tab)
        reports_group = QGroupBox("Reportes Generados")
        group_layout = QVBoxLayout()
        
        # Lista de reportes
        self.reports_list = QListWidget()
        self.reports_list.setMaximumHeight(140)
        self.reports_list.currentItemChanged.connect(lambda *_: self.show_report_details())
        
        # Botones de reportes
        reports_buttons = QHBoxLayout()
        self.refresh_reports_btn = QPushButton("🔄 Actualizar Lista")
        self.refresh_reports_btn.clicked.connect(self.refresh_reports)
        self.open_report_btn = QPushButton("📄 Abrir Reporte")
        self.open_report_btn.clicked.connect(self.open_selected_report)
        self.open_folder_btn = QPushButton("📁 Abrir Carpeta Reports")
        self.open_folder_btn.clicked.connect(self.open_reports_folder)
        
        reports_buttons.addWidget(self.refresh_reports_btn)
        reports_buttons.addWidget(self.open_report_btn)
        reports_buttons.addWidget(self.open_folder_btn)
        reports_buttons.addStretch()
        
        group_layout.addWidget(self.reports_list)
        group_layout.addLayout(reports_buttons)
        
        # Detalle del reporte seleccionado (incluye reglas dinámicas)
        self.report_details = QTextEdit()
        self.report_details.setReadOnly(True)
        self.report_details.setMinimumHeight(220)
        self.report_details.setFont(QFont("Consolas", 9))
        group_layout.addWidget(self.report_details)
        reports_group.setLayout(group_layout)
        reports_layout.addWidget(reports_group)
        
        # Cargar reportes iniciales
        self.refresh_reports()
        # Mostrar detalles del primer reporte si existe
        if self.reports_list.count() > 0:
            self.reports_list.setCurrentRow(0)
            self.show_report_details()

        return tab
        
    def apply_styles(self):
        """Aplicar estilos a la interfaz"""
        if self.dark_mode:
            self.setStyleSheet("""
                * { font-family: 'Manrope', 'Segoe UI', sans-serif; }
                QMainWindow, QWidget { background-color: #0b1220; color: #e5e7eb; }
                QTabWidget::pane {
                    border: 1px solid #1f2a3a;
                    border-radius: 8px;
                    padding: 6px;
                    background: #0f172a;
                }
                QTabBar::tab {
                    background: #1b2435;
                    border: 1px solid #1f2a3a;
                    border-radius: 6px;
                    padding: 8px 14px;
                    margin: 2px;
                    color: #e5e7eb;
                }
                QTabBar::tab:selected {
                    background: #2563eb;
                    color: #ffffff;
                    border-color: #1d4ed8;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #1f2a3a;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 12px;
                    background-color: #0f172a;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                    color: #e5e7eb;
                }
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    padding: 9px 14px;
                    border-radius: 6px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #1d4ed8; }
                QPushButton:pressed { background-color: #1e40af; }
                QPushButton:disabled {
                    background-color: #1f2a3a;
                    color: #6b7280;
                }
                QListWidget {
                    padding: 6px;
                    border: 1px solid #1f2a3a;
                    border-radius: 6px;
                    background-color: #0f172a;
                    color: #e5e7eb;
                }
                QProgressBar {
                    border: 1px solid #1f2a3a;
                    border-radius: 6px;
                    text-align: center;
                    background: #0f172a;
                    color: #e5e7eb;
                }
                QProgressBar::chunk { background-color: #2563eb; }
            """)
        else:
            self.setStyleSheet("""
                * { font-family: 'Manrope', 'Segoe UI', sans-serif; }
                QMainWindow, QWidget { background-color: #f7f8fb; }
                QTabWidget::pane {
                    border: 1px solid #d7dbe7;
                    border-radius: 8px;
                    padding: 6px;
                    background: #ffffff;
                }
                QTabBar::tab {
                    background: #e8ebf5;
                    border: 1px solid #d7dbe7;
                    border-radius: 6px;
                    padding: 8px 14px;
                    margin: 2px;
                }
                QTabBar::tab:selected {
                    background: #0066cc;
                    color: #ffffff;
                    border-color: #0052a3;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #d7dbe7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 12px;
                    background-color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                }
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    padding: 9px 14px;
                    border-radius: 6px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #0052a3; }
                QPushButton:pressed { background-color: #003d7a; }
                QPushButton:disabled {
                    background-color: #d1d5e0;
                    color: #7a8094;
                }
                QListWidget {
                    padding: 6px;
                    border: 1px solid #d7dbe7;
                    border-radius: 6px;
                    background-color: #ffffff;
                    color: #0a0f1a;
                }
                QProgressBar {
                    border: 1px solid #d7dbe7;
                    border-radius: 6px;
                    text-align: center;
                    background: #f0f2f8;
                }
                QProgressBar::chunk { background-color: #0066cc; }
            """)

    def apply_widget_theme(self):
        """Aplicar estilos específicos a widgets según el modo."""
        if self.dark_mode:
            input_bg = "#111a2d"; input_fg = "#e5e7eb"; border = "#2b3a55"; ph = "#9aa3b5"; sel_bg = "#2563eb"; sel_fg = "#e5e7eb"
            output_bg = "#0c1425"; output_fg = "#e5e7eb"
        else:
            input_bg = "#fdfdfd"; input_fg = "#0a0f1a"; border = "#c2ccde"; ph = "#7b8499"; sel_bg = "#cde2ff"; sel_fg = "#0a0f1a"
            output_bg = "#0f172a"; output_fg = "#e2e8f0"

        input_style = (
            f"background:{input_bg}; color:{input_fg}; border:1.2px solid {border}; border-radius:6px; padding:8px;"
            f"selection-background-color:{sel_bg}; selection-color:{sel_fg};"
        )
        placeholder_style = f"color:{ph};"
        combo_view_style = (
            f"background:{input_bg}; color:{input_fg}; selection-background-color:{sel_bg}; selection-color:{sel_fg};"
        )
        output_style = f"background:{output_bg}; color:{output_fg}; border:1px solid {border}; border-radius:6px; padding:8px;"

        for w in [
            getattr(self, name, None) for name in [
                "file_path_input", "folder_path_input", "level_combo",
                "user_input", "ruleset_name_input", "keywords_input", "required_input",
                "sample_text_input", "speech_input"
            ]
        ]:
            if w:
                w.setStyleSheet(input_style + (f" QLineEdit::placeholder{{{placeholder_style}}}" if isinstance(w, QLineEdit) else ""))
                if hasattr(w, "setMinimumHeight"):
                    w.setMinimumHeight(34)

        if hasattr(self, "level_combo"):
            self.level_combo.setStyleSheet(input_style)
            self.level_combo.view().setStyleSheet(combo_view_style)

        for w in [getattr(self, name, None) for name in ["ruleset_info", "sample_test_output", "log_text", "report_details"]]:
            if w:
                w.setStyleSheet(output_style)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_styles()
        self.apply_widget_theme()
        
    def check_directories(self):
        """Verificar y crear directorios necesarios"""
        root_dir = Path(__file__).parent.parent
        dirs = ['audio_in', 'reports', 'analysis', 'data']
        
        for d in dirs:
            dir_path = root_dir / d
            dir_path.mkdir(exist_ok=True)
            
        self.add_log(f"✓ Directorios verificados: {', '.join(dirs)}")
        self.refresh_ruleset_info()

    def refresh_ruleset_info(self):
        """Cargar el ruleset activo y mostrarlo"""
        try:
            active = self.rules_repo.get_active_ruleset(self.current_user_id)
            if not active:
                self.ruleset_info.setPlainText("No hay ruleset activo para este usuario. Guardá un preset o edita data/rulesets.json.")
                return

            text_lines = [
                f"Nombre: {active.name} (v{active.version})",
                f"ID: {active.id}",
                f"Usuario: {active.user_id} | Creado por: {active.created_by} en {active.created_at}",
                f"Keywords: {', '.join(active.keywords) if active.keywords else '—'}",
                f"Frases obligatorias: {', '.join(active.required_phrases) if active.required_phrases else '—'}",
                f"Umbrales: MEDIO>={active.thresholds.get('medium', 0)}, ALTO>={active.thresholds.get('high', 0)}, CRÍTICO>={active.thresholds.get('critical', 0)}",
                "Speech base:",
                active.template_text.strip()[:400] + ("..." if len(active.template_text) > 400 else ""),
            ]
            self.ruleset_info.setPlainText("\n".join(text_lines))
        except Exception as exc:
            self.ruleset_info.setPlainText(f"Error cargando reglas: {exc}")

    def on_user_changed(self, value: str):
        self.current_user_id = value.strip() or "default"
        self.refresh_ruleset_info()

    def save_ruleset_from_gui(self):
        """Guardar y activar ruleset para el usuario actual"""
        user_id = self.user_input.text().strip() or "default"
        name = self.ruleset_name_input.text().strip() or f"Preset {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        keywords = [k.strip() for k in self.keywords_input.text().split(",") if k.strip()]
        required = [k.strip() for k in self.required_input.text().split(",") if k.strip()]
        template_text = self.speech_input.toPlainText().strip()

        if not keywords and not required and not template_text:
            QMessageBox.warning(self, "Sin datos", "Agrega keywords, frases o speech base antes de guardar")
            return

        ruleset_id = f"{user_id}-{int(datetime.now().timestamp())}"
        data = {
            "id": ruleset_id,
            "name": name,
            "keywords": keywords,
            "required_phrases": required,
            "template_text": template_text,
            "thresholds": {
                "keyword_weight": 2,
                "missing_required_weight": 3,
                "similarity_weight": 5,
                "critical": 10,
                "high": 7,
                "medium": 4,
            },
            "created_by": user_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "version": 1,
            "active": True,
        }

        try:
            ruleset = RuleSet.from_dict(data)
            self.rules_repo.upsert(ruleset)
            self.rules_repo.activate(ruleset.id)
            self.current_user_id = user_id
            self.user_input.setText(user_id)
            QMessageBox.information(self, "Guardado", "Ruleset guardado y activado para el usuario")
            self.refresh_ruleset_info()
            self.apply_widget_theme()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo guardar el ruleset: {exc}")

    def run_sample_rules_test(self):
        """Probar el ruleset activo con un texto de ejemplo"""
        text = self.sample_text_input.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Sin texto", "Pega un texto de transcripción para probar")
            return

        ruleset = self.rules_repo.get_active_ruleset(self.current_user_id)
        if not ruleset:
            QMessageBox.warning(self, "Sin ruleset", "No hay ruleset activo para este usuario")
            return

        try:
            result = self.rules_engine.analyze(text, ruleset=ruleset, user_id=self.current_user_id)
            lines = [
                f"Ruleset: {result.get('ruleset_name', 'N/A')} (v{result.get('version', 'N/A')})",
                f"Nivel: {result.get('level', 'N/A')} | Score: {result.get('score', 0)}",
                f"Keywords detectadas: {', '.join(result.get('keywords_hit', [])) or '—'}",
                f"Frases faltantes: {', '.join(result.get('missing_required', [])) or '—'}",
                f"Similitud speech base: {result.get('similarity', 0):.2f}",
            ]
            self.sample_test_output.setPlainText("\n".join(lines))
        except Exception as exc:
            self.sample_test_output.setPlainText(f"Error al probar reglas: {exc}")

        
    def browse_file(self):
        """Abrir diálogo para seleccionar archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de audio",
            str(Path(__file__).parent.parent / "audio_in"),
            "Audio Files (*.wav *.mp3 *.m4a *.ogg *.flac);;All Files (*.*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
            self.add_log(f"Archivo seleccionado: {Path(file_path).name}")
            
    def browse_folder(self):
        """Abrir diálogo para seleccionar carpeta"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de audios",
            str(Path(__file__).parent.parent / "audio_in")
        )
        
        if folder_path:
            self.folder_path_input.setText(folder_path)
            self.add_log(f"Carpeta seleccionada: {folder_path}")
            
    def process_single_file(self):
        """Procesar archivo individual"""
        file_path = self.file_path_input.text()
        
        if not file_path or not Path(file_path).exists():
            QMessageBox.warning(
                self,
                "Error",
                "Por favor selecciona un archivo de audio válido"
            )
            return
            
        service_level = self.level_combo.currentText()
        
        self.add_log("="*70)
        self.add_log(f"Iniciando procesamiento de archivo individual")
        self.add_log(f"Archivo: {Path(file_path).name}")
        self.add_log(f"Nivel: {service_level}")
        self.add_log("="*70)
        
        # Deshabilitar botones
        self.set_processing_state(True)
        
        # Crear y ejecutar thread
        self.process_thread = ProcessThread(file_path, service_level, rules_user=self.current_user_id)
        self.process_thread.output_signal.connect(self.add_log)
        self.process_thread.finished_signal.connect(self.on_process_finished)
        self.process_thread.start()
        
    def process_batch(self):
        """Procesar carpeta completa"""
        folder_path = self.folder_path_input.text()
        
        if not folder_path or not Path(folder_path).exists():
            QMessageBox.warning(
                self,
                "Error",
                "Por favor selecciona una carpeta válida"
            )
            return
            
        self.add_log("="*70)
        self.add_log(f"Iniciando procesamiento en lote")
        self.add_log(f"Carpeta: {folder_path}")
        self.add_log("="*70)
        
        # Deshabilitar botones
        self.set_processing_state(True)
        
        # Crear y ejecutar thread
        self.process_thread = BatchProcessThread(folder_path, rules_user=self.current_user_id)
        self.process_thread.output_signal.connect(self.add_log)
        self.process_thread.finished_signal.connect(self.on_process_finished)
        self.process_thread.start()
        
    def stop_process(self):
        """Detener proceso actual"""
        if self.process_thread and self.process_thread.isRunning():
            if hasattr(self.process_thread, 'process') and self.process_thread.process:
                self.process_thread.process.terminate()
                self.add_log("⚠️ Proceso detenido por el usuario")
            self.process_thread.quit()
            self.process_thread.wait()
            self.set_processing_state(False)
            
    def on_process_finished(self, success, message):
        """Callback cuando el proceso termina"""
        self.set_processing_state(False)
        
        if success:
            self.add_log("="*70)
            self.add_log(f"✅ {message}")
            self.add_log("="*70)
            QMessageBox.information(self, "Éxito", message)
            self.refresh_reports()
        else:
            self.add_log("="*70)
            self.add_log(f"❌ {message}")
            self.add_log("="*70)
            QMessageBox.warning(self, "Error", message)
            
    def set_processing_state(self, processing):
        """Actualizar estado de la interfaz durante procesamiento"""
        self.process_file_btn.setEnabled(not processing)
        self.process_batch_btn.setEnabled(not processing)
        self.file_browse_btn.setEnabled(not processing)
        self.folder_browse_btn.setEnabled(not processing)
        self.level_combo.setEnabled(not processing)
        self.stop_btn.setEnabled(processing)
        
        if processing:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.statusBar().showMessage("Procesando...")
        else:
            self.progress_bar.setVisible(False)
            self.statusBar().showMessage("Listo")
            
    def add_log(self, message):
        """Agregar mensaje al log"""
        self.log_text.append(message)
        # Auto-scroll
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def clear_logs(self):
        """Limpiar logs"""
        self.log_text.clear()
        self.add_log("Logs limpiados")
        
    def refresh_reports(self):
        """Actualizar lista de reportes"""
        self.reports_list.clear()
        
        reports_dir = Path(__file__).parent.parent / "reports"
        if not reports_dir.exists():
            return
            
        # Buscar archivos JSON (más fáciles de procesar)
        json_files = sorted(
            reports_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for json_file in json_files[:20]:  # Últimos 20 reportes
            self.reports_list.addItem(json_file.name)
            
        self.add_log(f"📊 Lista de reportes actualizada: {len(json_files)} reportes encontrados")

        # Mostrar detalle del primero
        if self.reports_list.count() > 0:
            self.reports_list.setCurrentRow(0)
            self.show_report_details()

    def show_report_details(self):
        """Mostrar resumen del reporte seleccionado, incluyendo rules_engine"""
        selected_items = self.reports_list.selectedItems()
        if not selected_items:
            self.report_details.clear()
            return

        report_name = selected_items[0].text()
        reports_dir = Path(__file__).parent.parent / "reports"
        report_path = reports_dir / report_name
        if not report_path.exists():
            self.report_details.setPlainText("Reporte no encontrado")
            return

        try:
            with report_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)

            risk = data.get("risk", {})
            qa = data.get("qa", {})
            sentiment = data.get("sentiment", {})
            rules_engine = risk.get("rules_engine", {}) if isinstance(risk, dict) else {}

            overall_sent = sentiment.get("overall", {}) if isinstance(sentiment, dict) else {}
            sent_label = overall_sent.get("label", overall_sent) if isinstance(overall_sent, dict) else overall_sent

            qa_pct = data.get("qa_percentage", qa.get("compliance_percentage"))
            lines = [
                f"Archivo: {data.get('filename', 'N/A')}",
                f"Duración: {format_seconds(data.get('duration'))}",
                f"QA: {format_percentage(qa_pct, decimals=2)} ({qa.get('classification', 'N/A')})",
                f"Riesgo: {risk.get('level', 'N/A')} | Score: {risk.get('score', 'N/A')}",
                f"Sentimiento: {sent_label}",
                "",
                "Rules Engine (chat de reglas):",
            ]

            if rules_engine.get("enabled"):
                lines.extend([
                    f"  Ruleset: {rules_engine.get('ruleset_name', 'N/A')} v{rules_engine.get('version', 'N/A')} ({rules_engine.get('ruleset_id', '')})",
                    f"  Nivel: {rules_engine.get('level', 'N/A')} | Score: {rules_engine.get('score', 0)}",
                    f"  Keywords detectadas: {', '.join(rules_engine.get('keywords_hit', [])) or '—'}",
                    f"  Frases faltantes: {', '.join(rules_engine.get('missing_required', [])) or '—'}",
                    f"  Similitud speech base: {rules_engine.get('similarity', 0):.2f}",
                ])
            else:
                lines.append("  Reglas no habilitadas en este reporte")

            self.report_details.setPlainText("\n".join(lines))
        except Exception as exc:
            self.report_details.setPlainText(f"Error leyendo reporte: {exc}")
        
    def open_selected_report(self):
        """Abrir reporte seleccionado"""
        selected_items = self.reports_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Selecciona un reporte de la lista")
            return
            
        report_name = selected_items[0].text()
        reports_dir = Path(__file__).parent.parent / "reports"
        report_path = reports_dir / report_name
        
        if report_path.exists():
            # Abrir con aplicación predeterminada
            os.startfile(str(report_path))
            self.add_log(f"📄 Abriendo reporte: {report_name}")
        else:
            QMessageBox.warning(self, "Error", "Reporte no encontrado")
            
    def open_reports_folder(self):
        """Abrir carpeta de reportes"""
        reports_dir = Path(__file__).parent.parent / "reports"
        if reports_dir.exists():
            os.startfile(str(reports_dir))
            self.add_log("📁 Abriendo carpeta de reportes")
        else:
            QMessageBox.warning(self, "Error", "Carpeta de reportes no encontrada")


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno
    
    window = DAIAMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
