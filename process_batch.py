#!/usr/bin/env python3
"""
DAIA Batch Processor - Script completo de procesamiento masivo

USO:
    python process_batch.py audio_in/ --service-level standard --format both
    
EJEMPLO:
    python process_batch.py audio_in/ --format pdf
    python process_batch.py C:/audios/enero/ --service-level advanced
"""

import sys
import argparse
import logging
import shutil
from pathlib import Path
from typing import List, Optional

# Agregar scripts al path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from daia.application import process_audio_folder
from daia.infrastructure import generate_batch_reports, generate_individual_reports
try:
    from daia.infrastructure.drive import (
        DriveClient,
        load_drive_config,
        resolve_client_folders,
        pull_pending_audios,
        push_reports,
        move_audios,
    )
    from daia.infrastructure.drive.drive_types import DownloadedAudio, ClientFolders
    DRIVE_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # Drive is optional; keep pipeline running without it
    DRIVE_IMPORT_ERROR = exc
    DriveClient = None  # type: ignore
    load_drive_config = None  # type: ignore
    resolve_client_folders = None  # type: ignore
    pull_pending_audios = None  # type: ignore
    push_reports = None  # type: ignore
    move_audios = None  # type: ignore
    DownloadedAudio = None  # type: ignore
    ClientFolders = None  # type: ignore

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='DAIA 2.0 - Procesador Batch de Auditorías',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s audio_in/                              # Procesa carpeta con defaults
  %(prog)s audio_in/ --format pdf                 # Solo PDF
  %(prog)s audio_in/ --service-level advanced     # Auditoría avanzada
  %(prog)s C:/audios/enero/ --no-individual       # Solo consolidado
        """
    )
    
    parser.add_argument(
        'folder',
        help='Ruta de la carpeta con archivos de audio'
    )
    
    parser.add_argument(
        '--service-level',
        choices=['basic', 'standard', 'advanced'],
        default='standard',
        help='Nivel de auditoría (default: standard)'
    )
    
    parser.add_argument(
        '--format',
        choices=['pdf', 'docx', 'both'],
        default='both',
        help='Formato de reportes (default: both)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='reports',
        help='Directorio de salida para reportes (default: reports)'
    )
    
    parser.add_argument(
        '--no-individual',
        action='store_true',
        help='No generar reportes individuales (solo consolidado)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose (más detalles)'
    )

    parser.add_argument(
        '--drive-client',
        help='Nombre de carpeta de cliente en Drive (habilita modo Drive)'
    )

    parser.add_argument(
        '--drive-root-id',
        help='Override opcional del ID de carpeta clientes/ (env DRIVE_CLIENTS_ROOT_ID si no)'
    )

    parser.add_argument(
        '--drive-service-account',
        help='Ruta al JSON de service account para Drive (env DRIVE_SERVICE_ACCOUNT_FILE si no)'
    )

    parser.add_argument(
        '--drive-temp-dir',
        default='audio_in/tmp_drive',
        help='Carpeta temporal local para audios descargados (default: audio_in/tmp_drive)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar carpeta (excepto si solo se usa Drive)
    folder_path = Path(args.folder)
    if not folder_path.exists():
        if args.drive_client:
            logger.warning(
                f"⚠️ Carpeta local no existe ({args.folder}); se usará únicamente Drive si está disponible"
            )
        else:
            logger.error(f"❌ Carpeta no existe: {args.folder}")
            return 1
    
    logger.info("=" * 70)
    logger.info("DAIA 2.0 - PROCESADOR BATCH DE AUDITORÍAS")
    logger.info("=" * 70)
    logger.info(f"📁 Carpeta: {folder_path.absolute()}")
    logger.info(f"🎯 Nivel: {args.service_level}")
    logger.info(f"📄 Formato: {args.format}")
    logger.info(f"💾 Output: {args.output_dir}")
    logger.info("=" * 70)
    
    drive_enabled = bool(args.drive_client)
    drive_client: Optional[DriveClient] = None
    client_folders: Optional[ClientFolders] = None
    downloads: List[DownloadedAudio] = []
    processing_folder = folder_path
    drive_active_session = False

    if drive_enabled and DRIVE_IMPORT_ERROR:
        logger.warning(
            "⚠️ Dependencias de Drive no instaladas; modo Drive deshabilitado (%s)",
            DRIVE_IMPORT_ERROR,
        )
        drive_enabled = False

    if drive_enabled:
        try:
            drive_cfg = load_drive_config(
                Path("config.yaml"),
                root_id_override=args.drive_root_id,
                service_account_override=args.drive_service_account,
            )
            if DriveClient and resolve_client_folders:
                drive_client = DriveClient(drive_cfg.service_account_file)
                client_folders = resolve_client_folders(
                    drive_client, drive_cfg, args.drive_client
                )
            else:
                raise RuntimeError("Drive modules not available")

            if client_folders:
                tmp_dir = Path(args.drive_temp_dir)
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir)
                tmp_dir.mkdir(parents=True, exist_ok=True)

                downloads = pull_pending_audios(drive_client, client_folders, tmp_dir)
                if downloads:
                    processing_folder = tmp_dir
                    drive_active_session = True
                    logger.info(
                        "🟢 Drive habilitado: %d audio(s) descargados para %s",
                        len(downloads),
                        args.drive_client,
                    )
                else:
                    logger.warning(
                        "⚠️ Sin audios pendientes en Drive para %s; se usa carpeta local %s",
                        args.drive_client,
                        folder_path,
                    )
            else:
                logger.warning(
                    "⚠️ Cliente Drive no encontrado (%s); modo Drive deshabilitado",
                    args.drive_client,
                )
                drive_enabled = False
        except Exception as exc:
            logger.warning("⚠️ Drive deshabilitado por error: %s", exc)
            drive_enabled = False

    try:
        report_paths: List[Path] = []
        success_with_reports: set[str] = set()

        # 1. PROCESAR BATCH
        logger.info("\n🚀 FASE 1: Procesando audios...")
        batch_result = process_audio_folder(str(processing_folder), args.service_level)
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 RESULTADOS DEL BATCH")
        logger.info("=" * 70)
        
        summary = batch_result.summary_dict()
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
        
        # 2. GENERAR REPORTE CONSOLIDADO
        logger.info("\n📝 FASE 2: Generando reporte consolidado...")
        consolidated_reports = generate_batch_reports(
            batch_result,
            output_dir=args.output_dir,
            format=args.format
        )
        report_paths.extend(Path(p) for p in consolidated_reports.values())
        
        logger.info("✅ Reportes consolidados generados:")
        for fmt, path in consolidated_reports.items():
            logger.info(f"  {fmt.upper()}: {path}")
        
        # 3. GENERAR REPORTES INDIVIDUALES (opcional)
        if not args.no_individual:
            logger.info("\n📝 FASE 3: Generando reportes individuales...")
            individual_count = 0
            
            for result in batch_result.results:
                try:
                    reports = generate_individual_reports(
                        result,
                        output_dir=args.output_dir,
                        format=args.format
                    )
                    individual_count += len(reports)
                    for p in reports.values():
                        report_paths.append(Path(p))
                    # Success only if a report was produced for this audio
                    if reports:
                        success_with_reports.add(result.audited_call.filename)
                except Exception as e:
                    logger.warning(f"  ⚠️ Error en {result.audited_call.filename}: {e}")
            
            logger.info(f"✅ {individual_count} reportes individuales generados")
        else:
            logger.info("\n⏩ Reportes individuales omitidos (--no-individual)")

        if drive_active_session and drive_client and client_folders:
            # Success criterion: pipeline produced reports for the audio (or at least one individual report succeeded)
            success_names = success_with_reports or {r.audited_call.filename for r in batch_result.results}
            download_map = {item.local_path.name: item for item in downloads}

            success_items = [item for name, item in download_map.items() if name in success_names]
            failure_items = [item for name, item in download_map.items() if name not in success_names]

            if report_paths:
                push_reports(drive_client, client_folders, report_paths)

            move_audios(drive_client, client_folders, success_items, failure_items)
        
        # 4. RESUMEN FINAL
        logger.info("\n" + "=" * 70)
        logger.info("✅ PROCESO COMPLETADO")
        logger.info("=" * 70)
        logger.info(f"✓ {batch_result.total_calls} audios procesados")
        logger.info(f"✓ {batch_result.passed_calls} aprobados ({batch_result.approval_rate:.1f}%)")
        logger.info(f"✓ QA Score promedio: {batch_result.avg_qa_score:.1f}%")
        
        if batch_result.critical_findings_count > 0:
            logger.warning(f"⚠️  {batch_result.critical_findings_count} hallazgos críticos detectados")
        
        logger.info(f"\n📂 Reportes guardados en: {Path(args.output_dir).absolute()}")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
