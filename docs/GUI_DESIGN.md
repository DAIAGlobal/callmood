# 🖼️ DAIA 2.0 GUI - Características Visuales

## 🎨 Diseño de la Interfaz

### Ventana Principal

```
┌─────────────────────────────────────────────────────────────────────┐
│  DAIA 2.0 - Sistema de Auditoría de Llamadas               [_][□][X]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ╔═══════════════════════════════════════════════════════════╗   │
│   ║                       DAIA 2.0                            ║   │
│   ║     Sistema de Auditoría y Compliance - 100% Local       ║   │
│   ╚═══════════════════════════════════════════════════════════╝   │
│                                                                     │
│   ╔═════════════════ Panel de Control ═════════════════════╗      │
│   ║                                                          ║      │
│   ║  Archivo de audio:  [_______________________] [📁 Explorar] ║  │
│   ║                                                          ║      │
│   ║  Carpeta de audios: [____audio_in/__________] [📁 Explorar] ║  │
│   ║                                                          ║      │
│   ║  Nivel de análisis: [standard ▼]                        ║      │
│   ║                                                          ║      │
│   ║  [🎙️ Procesar Archivo Individual] [📊 Procesar Carpeta]  ║      │
│   ║  [⛔ Detener]                                            ║      │
│   ║                                                          ║      │
│   ║  [████████████████████] Procesando...                   ║      │
│   ╚═══════════════════════════════════════════════════════════╝   │
│                                                                     │
│   ╔═════════════════ Logs de Procesamiento ═══════════════╗       │
│   ║                                                         ║       │
│   ║  2026-01-01 18:30:00 - [INFO] Iniciando proceso...     ║       │
│   ║  2026-01-01 18:30:01 - [INFO] Transcribiendo audio...  ║       │
│   ║  2026-01-01 18:30:05 - [INFO] Analizando sentimiento...║       │
│   ║  2026-01-01 18:30:10 - [INFO] ✓ Procesamiento exitoso ║       │
│   ║                                                         ║       │
│   ║                                    [🗑️ Limpiar Logs]   ║       │
│   ╚═══════════════════════════════════════════════════════════╝   │
│                                                                     │
│   ╔═════════════════ Reportes Generados ══════════════════╗       │
│   ║                                                         ║       │
│   ║  • 20260101_183059_Grabación_de_llamada_1929.json      ║       │
│   ║  • 20260101_182803_Grabación_de_llamada_1929.json      ║       │
│   ║  • 20260101_182530_Grabación_de_llamada_1929.json      ║       │
│   ║                                                         ║       │
│   ║  [🔄 Actualizar] [📄 Abrir Reporte] [📁 Abrir Carpeta] ║       │
│   ╚═══════════════════════════════════════════════════════════╝   │
│                                                                     │
│  Estado: Listo                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Características Visuales

### 1. Header (Encabezado)
- **Título grande**: "DAIA 2.0" en Arial 24pt, negrita
- **Subtítulo**: "Sistema de Auditoría y Compliance - 100% Local"
- **Estilo**: Fondo blanco, centrado, bordes suaves

### 2. Panel de Control
- **Etiquetas claras**: Con ancho fijo para alineación
- **Campos de entrada**: 
  - Color blanco con borde gris (#cccccc)
  - Bordes redondeados (4px)
  - Placeholders informativos
- **Botones de exploración**: 
  - Icono 📁 + "Explorar"
  - Color azul corporativo (#0066cc)
- **Combo box**: Desplegable con 3 opciones
- **Botones de acción**:
  - Altura: 40px
  - Color: Azul (#0066cc)
  - Hover: Azul oscuro (#0052a3)
  - Disabled: Gris (#cccccc)
- **Barra de progreso**:
  - Solo visible durante procesamiento
  - Modo indeterminado (animación continua)
  - Color azul matching los botones

### 3. Panel de Logs
- **Fondo oscuro**: #1e1e1e (estilo VS Code)
- **Texto**: Color claro #d4d4d4
- **Fuente**: Consolas/Courier New (monospace) 9pt
- **Auto-scroll**: Se desplaza automáticamente al final
- **Read-only**: No editable por usuario
- **Altura mínima**: 250px

### 4. Panel de Reportes
- **Lista de archivos**:
  - Fondo blanco
  - Borde gris suave
  - Altura máxima: 120px
  - Scroll automático si hay muchos reportes
- **Botones**:
  - 🔄 Actualizar Lista
  - 📄 Abrir Reporte
  - 📁 Abrir Carpeta Reports
  - Mismos estilos que botones principales

### 5. Barra de Estado (Bottom)
- **Posición**: Parte inferior de la ventana
- **Estados**:
  - "Listo" (por defecto)
  - "Procesando..." (durante operación)
  - Mensajes contextuales

## 🎨 Paleta de Colores

### Principales
```
Azul Corporativo:   #0066cc (Botones, acciones)
Azul Hover:         #0052a3 (Botones al pasar mouse)
Azul Pressed:       #003d7a (Botones al hacer clic)
Gris Deshabilitado: #cccccc (Botones inactivos)
Gris Bordes:        #cccccc (Bordes de inputs)
```

### Backgrounds
```
Ventana:            #f5f5f5 (Gris muy claro)
Paneles:            #ffffff (Blanco)
Logs:               #1e1e1e (Oscuro)
```

### Textos
```
Principal:          #000000 (Negro)
Secundario:         #666666 (Gris)
Logs:               #d4d4d4 (Claro sobre oscuro)
```

## 📐 Dimensiones

### Ventana Principal
- **Tamaño mínimo**: 1000 x 700 px
- **Responsive**: Se adapta al tamaño
- **Márgenes**: 15px todos los lados
- **Espaciado**: 10px entre componentes

### Componentes
- **Botones estándar**: auto x 35px
- **Botones grandes**: auto x 40px
- **Inputs**: stretch x 30px
- **Panel Logs**: auto x 250px (mínimo)
- **Panel Reportes**: auto x 120px (máximo)

## 🎭 Estados de la Interfaz

### Estado Inicial (Listo)
```
✅ Todos los botones habilitados
✅ Barra de progreso oculta
✅ Status: "Listo"
✅ Lista de reportes cargada
```

### Estado Procesando
```
⛔ Botones de proceso deshabilitados
✅ Botón Detener habilitado
✅ Barra de progreso visible y animada
✅ Status: "Procesando..."
✅ Logs actualizándose en tiempo real
```

### Estado Error
```
❌ Modal con mensaje de error
✅ Todos los botones vuelven a habilitar
✅ Barra de progreso oculta
✅ Status: "Error"
```

### Estado Completado
```
✅ Modal de confirmación
✅ Lista de reportes actualizada
✅ Todos los botones habilitados
✅ Status: "Listo"
```

## 🖱️ Interacciones

### Botones con Hover
```
Normal:    Azul (#0066cc)
  ↓
Hover:     Azul oscuro (#0052a3)
  ↓
Click:     Azul muy oscuro (#003d7a)
```

### Campos de Entrada
```
Normal:    Borde gris (#cccccc)
  ↓
Focus:     Borde más marcado
```

### Lista de Reportes
```
Item no seleccionado:  Fondo blanco
  ↓
Hover:                 Fondo gris muy claro
  ↓
Seleccionado:          Fondo azul claro
```

## 🎬 Animaciones

### Barra de Progreso
- **Tipo**: Indeterminada (movimiento continuo)
- **Velocidad**: Media
- **Color**: Azul matching los botones

### Transiciones
- **Hover en botones**: 150ms ease
- **Show/Hide progreso**: Instant
- **Scroll logs**: Smooth

## 📱 Responsive Design

### Ventana Pequeña (1000x700)
- Diseño vertical estándar
- Todos los componentes visibles
- Scroll en logs y reportes si necesario

### Ventana Grande (1920x1080+)
- Mayor espacio para logs
- Lista de reportes más grande
- Mejor legibilidad

## 🎪 Feedback Visual

### Mensajes de Confirmación
```
┌─────────────────────────────┐
│  ✅ Éxito                    │
│                             │
│  Procesamiento completado   │
│  exitosamente              │
│                             │
│          [ OK ]             │
└─────────────────────────────┘
```

### Mensajes de Error
```
┌─────────────────────────────┐
│  ❌ Error                    │
│                             │
│  Por favor selecciona un    │
│  archivo de audio válido    │
│                             │
│          [ OK ]             │
└─────────────────────────────┘
```

### Mensajes de Advertencia
```
┌─────────────────────────────┐
│  ⚠️ Advertencia              │
│                             │
│  ¿Estás seguro de detener   │
│  el proceso actual?         │
│                             │
│     [ Sí ]    [ No ]        │
└─────────────────────────────┘
```

## 🔤 Tipografía

### Fuentes
- **UI Principal**: System default (Segoe UI en Windows)
- **Títulos**: Arial, negrita
- **Logs**: Consolas / Courier New (monospace)

### Tamaños
- **Título principal**: 24pt
- **Subtítulo**: 11pt
- **Labels**: 9pt
- **Botones**: 9pt, negrita
- **Logs**: 9pt

## 🎨 Iconos y Emojis

### Iconos Usados
- 📁 Explorar
- 🎙️ Procesar Archivo
- 📊 Procesar Carpeta
- ⛔ Detener
- 🗑️ Limpiar
- 🔄 Actualizar
- 📄 Abrir Reporte
- 📁 Abrir Carpeta

### En Logs
- ✅ / ✓ Operación exitosa
- ❌ Error
- ⚠️ Advertencia
- 🎙️ Transcripción
- 😊 Sentimiento
- 📊 Análisis

## 📏 Layouts

### Estructura Jerárquica
```
QMainWindow
└── QWidget (central)
    └── QVBoxLayout (main)
        ├── QGroupBox (Header)
        │   └── QVBoxLayout
        │       ├── QLabel (Title)
        │       └── QLabel (Subtitle)
        │
        ├── QGroupBox (Control Panel)
        │   └── QVBoxLayout
        │       ├── QHBoxLayout (File selector)
        │       ├── QHBoxLayout (Folder selector)
        │       ├── QHBoxLayout (Level selector)
        │       ├── QHBoxLayout (Action buttons)
        │       └── QProgressBar
        │
        ├── QGroupBox (Logs Panel)
        │   └── QVBoxLayout
        │       ├── QTextEdit (logs)
        │       └── QHBoxLayout (buttons)
        │
        └── QGroupBox (Reports Panel)
            └── QVBoxLayout
                ├── QListWidget
                └── QHBoxLayout (buttons)
```

## 🎓 Resumen de Experiencia Visual

La interfaz gráfica de DAIA 2.0 ofrece:

✅ **Diseño profesional** y moderno
✅ **Colores corporativos** consistentes
✅ **Feedback visual claro** en cada acción
✅ **Organización lógica** de componentes
✅ **Accesibilidad** con tamaños de fuente legibles
✅ **Responsive** a diferentes tamaños de ventana
✅ **Iconografía clara** con emojis universales
✅ **Estados visuales distintos** para cada situación

**Objetivo**: Proporcionar una experiencia de usuario **intuitiva, clara y profesional** que haga el sistema accesible para usuarios no técnicos sin comprometer la funcionalidad.
