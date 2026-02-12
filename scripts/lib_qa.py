"""
DAIA - QA Module (Rule-Based, No AI Cost)
Control de calidad mediante reglas declarativas YAML.
100% Local, 0 USD, Control Total.
"""

import logging
import re
from typing import Dict, List, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class QARuleEngine:
    """Motor de reglas QA basado en patrones declarativos"""
    
    def __init__(self, rules: Dict[str, Any]):
        """
        Inicializa el motor QA.
        
        Args:
            rules: Configuración de reglas desde config.yaml
        """
        self.rules = rules
        self.results = {}
    
    def evaluate_call(self, transcript: str, level: str = "standard") -> Dict[str, Any]:
        """
        Evalúa una transcripción contra reglas QA.
        
        Args:
            transcript: Texto de la transcripción
            level: Nivel de evaluación ('basic', 'standard', 'advanced')
            
        Returns:
            dict: Resultados de la evaluación
        """
        text_lower = transcript.lower()
        
        # Obtener reglas del nivel
        level_rules = self.rules.get(level, self.rules['standard'])
        
        result = {
            'level': level,
            'transcript_length': len(transcript),
            'checks': {},
            'score': 0,
            'max_score': 0,
            'compliance_percentage': 0,
            'details': []
        }
        
        # 1. Verificar frases obligatorias
        mandatory_check = self._check_mandatory_phrases(
            text_lower,
            level_rules.get('mandatory_phrases', [])
        )
        result['checks']['mandatory_phrases'] = mandatory_check
        result['details'].append(mandatory_check)
        
        # 2. Verificar frases prohibidas
        forbidden_check = self._check_forbidden_phrases(
            text_lower,
            level_rules.get('forbidden_phrases', [])
        )
        result['checks']['forbidden_phrases'] = forbidden_check
        result['details'].append(forbidden_check)
        
        # 3. Verificar duración mínima
        if 'min_duration_seconds' in level_rules:
            duration_check = self._check_minimum_duration(
                transcript,
                level_rules['min_duration_seconds']
            )
            result['checks']['duration'] = duration_check
            result['details'].append(duration_check)
        
        # 4. Verificar ratio de silencios
        if 'max_silence_ratio' in level_rules:
            silence_check = self._check_silence_ratio(
                transcript,
                level_rules['max_silence_ratio']
            )
            result['checks']['silence'] = silence_check
            result['details'].append(silence_check)
        
        # 5. Elementos requeridos (advanced)
        if 'required_elements' in level_rules:
            elements_check = self._check_required_elements(
                text_lower,
                level_rules.get('required_elements', [])
            )
            result['checks']['required_elements'] = elements_check
            result['details'].append(elements_check)
        
        # 6. Palabras de calidad (advanced)
        if 'quality_keywords' in level_rules:
            quality_check = self._check_quality_keywords(
                text_lower,
                level_rules['quality_keywords']
            )
            result['checks']['quality'] = quality_check
            result['details'].append(quality_check)
        
        # Calcular score final
        result = self._calculate_final_score(result, level_rules)
        
        return result
    
    def _check_mandatory_phrases(self, text: str, phrases: List[str]) -> Dict:
        """Verifica presencia de frases obligatorias"""
        found = []
        missing = []
        
        for phrase in phrases:
            if self._phrase_in_text(text, phrase):
                found.append(phrase)
            else:
                missing.append(phrase)
        
        compliance = len(found) / len(phrases) if phrases else 0
        
        return {
            'name': 'Frases Obligatorias',
            'type': 'mandatory',
            'total': len(phrases),
            'found': len(found),
            'missing': len(missing),
            'compliance': compliance,
            'status': 'OK' if not missing else 'FALLO',
            'details': {
                'found': found,
                'missing': missing
            },
            'weight': 0.4
        }
    
    def _check_forbidden_phrases(self, text: str, phrases: List[str]) -> Dict:
        """Verifica ausencia de frases prohibidas"""
        found = []
        
        for phrase in phrases:
            count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text))
            if count > 0:
                found.append((phrase, count))
        
        result = {
            'name': 'Frases Prohibidas',
            'type': 'forbidden',
            'total': len(phrases),
            'violations': len(found),
            'compliance': 0 if found else 1,
            'status': 'OK' if not found else 'FALLO',
            'details': {
                'violations': found
            },
            'weight': 0.3
        }
        
        return result
    
    def _check_minimum_duration(self, transcript: str, min_seconds: int) -> Dict:
        """Verifica duración mínima aproximada por palabra count"""
        # Aproximación: ~150 palabras por minuto = 2.5 palabras/segundo
        word_count = len(transcript.split())
        estimated_duration = word_count / 2.5
        
        complies = estimated_duration >= min_seconds
        
        return {
            'name': 'Duración Mínima',
            'type': 'duration',
            'minimum_seconds': min_seconds,
            'estimated_duration': estimated_duration,
            'compliance': 1.0 if complies else estimated_duration / min_seconds,
            'status': 'OK' if complies else 'CORTO',
            'details': {
                'required': f"{min_seconds}s",
                'estimated': f"{estimated_duration:.0f}s"
            },
            'weight': 0.2
        }
    
    def _check_silence_ratio(self, transcript: str, max_ratio: float) -> Dict:
        """Verifica ratio de silencios (simplificado)"""
        # Simplificación: contar líneas en blanco
        lines = transcript.split('\n')
        empty_lines = len([l for l in lines if not l.strip()])
        total_lines = len([l for l in lines if l.strip()])
        
        silence_ratio = empty_lines / (empty_lines + total_lines) if (empty_lines + total_lines) > 0 else 0
        complies = silence_ratio <= max_ratio
        
        return {
            'name': 'Ratio de Silencios',
            'type': 'silence',
            'maximum_ratio': max_ratio,
            'actual_ratio': silence_ratio,
            'compliance': 1.0 if complies else (1 - silence_ratio / max_ratio),
            'status': 'OK' if complies else 'EXCESO',
            'details': {
                'max': f"{max_ratio*100:.0f}%",
                'actual': f"{silence_ratio*100:.1f}%"
            },
            'weight': 0.15
        }
    
    def _check_required_elements(self, text: str, elements: List[str]) -> Dict:
        """Verifica presencia de elementos requeridos (conceptos)"""
        found = []
        missing = []
        
        # Mapeo de conceptos a palabras clave
        concept_keywords = {
            'problema identificado': ['problema', 'identificado', 'issue', 'issue'],
            'solución ofrecida': ['solución', 'ofrecida', 'resuelto', 'solucionado'],
            'despedida cortés': ['gracias', 'adiós', 'hasta luego', 'saludos'],
            'empatía demostrada': ['entiendo', 'comprendo', 'lamento', 'disculpe'],
            'solución probada': ['probado', 'funciona', 'funcionó', 'verificado'],
            'confirmación del cliente': ['confirma', 'acuerdo', 'conforme', 'de acuerdo'],
            'seguimiento ofrecido': ['seguimiento', 'voy a', 'próximo', 'contacto']
        }
        
        for element in elements:
            keywords = concept_keywords.get(element, [element])
            found_any = any(self._phrase_in_text(text, kw) for kw in keywords)
            
            if found_any:
                found.append(element)
            else:
                missing.append(element)
        
        compliance = len(found) / len(elements) if elements else 0
        
        return {
            'name': 'Elementos Requeridos',
            'type': 'elements',
            'total': len(elements),
            'found': len(found),
            'compliance': compliance,
            'status': 'OK' if not missing else 'INCOMPLETO',
            'details': {
                'found': found,
                'missing': missing
            },
            'weight': 0.25
        }
    
    def _check_quality_keywords(self, text: str, keywords: List[str]) -> Dict:
        """Verifica presencia de palabras de calidad"""
        found = []
        count = 0
        
        for keyword in keywords:
            occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            if occurrences > 0:
                found.append((keyword, occurrences))
                count += occurrences
        
        # Score: más palabras de calidad = mejor
        compliance = min(1.0, count / len(keywords)) if keywords else 0
        
        return {
            'name': 'Palabras de Calidad',
            'type': 'quality',
            'target_keywords': len(keywords),
            'found_keywords': len(found),
            'total_occurrences': count,
            'compliance': compliance,
            'status': 'OK' if found else 'AUSENTES',
            'details': {
                'keywords_found': found
            },
            'weight': 0.2
        }
    
    def _calculate_final_score(self, result: Dict, level_rules: Dict) -> Dict:
        """Calcula score final ponderado"""
        total_weight = 0
        weighted_score = 0
        
        for check in result['details']:
            weight = check.get('weight', 0.2)
            compliance = check.get('compliance', 0)
            
            total_weight += weight
            weighted_score += compliance * weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        result['score'] = final_score
        result['max_score'] = 1.0
        result['compliance_percentage'] = final_score * 100
        
        # Clasificación según estándares de call center
        # Estándares profesionales: 85%+ Excelente, 70-84% Bueno, 50-69% Aceptable, <50% Deficiente
        if final_score >= 0.85:
            result['classification'] = 'EXCELENTE'
        elif final_score >= 0.70:
            result['classification'] = 'BUENO'
        elif final_score >= 0.50:
            result['classification'] = 'ACEPTABLE'
        elif final_score >= 0.30:
            result['classification'] = 'DEFICIENTE'
        else:
            result['classification'] = 'CRÍTICO'
        
        return result
    
    def _phrase_in_text(self, text: str, phrase: str) -> bool:
        """Busca una frase en el texto (case-insensitive, flexible)"""
        phrase_lower = phrase.lower()
        return phrase_lower in text
    
    def get_summary(self, result: Dict) -> str:
        """Genera resumen textual del resultado QA"""
        summary = f"""
EVALUACIÓN QA - {result['level'].upper()}
{'='*50}
Clasificación: {result.get('classification', 'N/A')}
Cumplimiento: {result['compliance_percentage']:.1f}%
Score: {result['score']:.2f}/{result['max_score']:.2f}

DETALLES POR CATEGORÍA:
"""
        for check in result['details']:
            summary += f"\n  • {check['name']}: {check['status']}"
            if 'details' in check and isinstance(check['details'], dict):
                if 'missing' in check['details'] and check['details']['missing']:
                    summary += f"\n    - Faltantes: {', '.join(check['details']['missing'][:3])}"
                if 'violations' in check['details'] and check['details']['violations']:
                    summary += f"\n    - Violaciones: {len(check['details']['violations'])}"
        
        return summary


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cargar reglas desde config.yaml
    from lib_resources import ConfigManager
    
    config = ConfigManager("../config.yaml")
    rules = config.get("qa.rules")
    
    # Crear motor QA
    qa_engine = QARuleEngine(rules)
    
    # Ejemplo de transcripción
    test_transcript = """
    Buenos días, ¿cómo puedo ayudarle?
    Hola, tengo un problema con mi cuenta.
    Entiendo perfectamente. Voy a resolver esto.
    ¿Cuál es su número de cliente?
    Es el 123456.
    Gracias. Un momento... Listo, su problema está resuelto.
    Perfecto, muchas gracias por su ayuda.
    A usted. Que tenga un excelente día.
    """
    
    # Evaluar
    result = qa_engine.evaluate_call(test_transcript, "standard")
    print(qa_engine.get_summary(result))
