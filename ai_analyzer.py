import os
from openai import OpenAI
from typing import Dict, Any
import json

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def format_resume_for_analysis(full_resume: Dict[str, Any]) -> str:
    """Форматирует резюме из HH.ru в читаемый текст"""
    text = ""
    
    if not full_resume:
        return "Нет данных для анализа."
    
    # Опыт работы
    if full_resume.get('experience'):
        text += "Опыт работы:\n"
        for exp in full_resume['experience']:
            text += f"- {exp.get('position', '')} в {exp.get('company', '')} "
            text += f"({exp.get('start', '')} - {exp.get('end', 'н.в.')})\n"
            if exp.get('description'):
                # Убираем HTML теги
                desc = exp['description'].replace('<', ' <').replace('>', '> ')
                import re
                desc = re.sub('<[^>]+>', '', desc)
                text += f"  Описание: {desc}\n"
    
    # Образование
    if full_resume.get('education', {}).get('primary'):
        text += "\nОбразование:\n"
        for edu in full_resume['education']['primary']:
            text += f"- {edu.get('name', '')} ({edu.get('year', '')}, {edu.get('result', '')})\n"
    
    # Навыки
    if full_resume.get('skill_set'):
        text += f"\nНавыки: {', '.join(full_resume['skill_set'])}\n"
    
    # Зарплата
    if full_resume.get('salary'):
        amount = full_resume['salary'].get('amount', '')
        currency = full_resume['salary'].get('currency', '')
        text += f"\nЖелаемая зарплата: {amount} {currency}\n"
    
    return text

def analyze_resume(resume_text: str, criteria: str = None) -> Dict[str, Any]:
    """
    Анализирует резюме через OpenAI
    
    Args:
        resume_text: Текст резюме
        criteria: Критерии оценки (опционально)
    
    Returns:
        Dict с verdict, reason
    """
    
    if not criteria:
        criteria = "Оцени кандидата на адекватность и соответствие стандартным требованиям."
    
    prompt = f"""Проанализируй резюме кандидата по следующим критериям:
{criteria}

Резюме:
{resume_text}

Выдай свой вердикт в формате JSON:
{{
    "verdict": "Подходит" или "Не подходит",
    "reason": "Краткая причина (1-2 предложения)"
}}

Важно: Отвечай ТОЛЬКО JSON, без дополнительного текста."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты HR-аналитик. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        return {
            "status": "success",
            "verdict": result.get("verdict", "Не определено"),
            "reason": result.get("reason", "")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def analyze_resume_from_hh(full_resume: Dict[str, Any], criteria: str = None) -> Dict[str, Any]:
    """
    Анализирует резюме напрямую из данных HH.ru
    
    Args:
        full_resume: Полный объект резюме от HH.ru
        criteria: Критерии оценки
    
    Returns:
        Dict с результатами анализа
    """
    resume_text = format_resume_for_analysis(full_resume)
    return analyze_resume(resume_text, criteria)

        # Экспорт функций
    __all__ = ['analyze_resume', 'analyze_resume_from_hh', 'format_resume_for_analysis']