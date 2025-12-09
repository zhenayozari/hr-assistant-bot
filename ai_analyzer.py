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
    Анализирует резюме через OpenAI С ПОДСЧЁТОМ СОВПАДЕНИЙ
    
    Args:
        resume_text: Текст резюме
        criteria: Критерии оценки (опционально)
    
    Returns:
        Dict с verdict, reason, matches_count, matched_criteria
    """
    
    if not criteria:
        criteria = "Оцени кандидата на адекватность и соответствие стандартным требованиям."
    
    prompt = f"""Ты HR-эксперт. Анализируй СТРОГО по критериям.

ПРАВИЛО: Из всех критериев должно совпадать НЕ МЕНЕЕ 3. Иначе — "Не подходит".

Критерии вакансии:
{criteria}

Резюме кандидата:
{resume_text}

Верни СТРОГО JSON:
{{
    "verdict": "Подходит" или "Не подходит",
    "reason": "Одно короткое предложение (главный аргумент)",
    "matches_count": число_совпавших_критериев,
    "matched_criteria": ["критерий 1", "критерий 2", ...]
}}

Важно: Отвечай ТОЛЬКО JSON, без дополнительного текста."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты HR-эксперт. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Проверка минимум 3 совпадения
        matches = result.get("matches_count", 0)
        if matches < 3 and result.get("verdict") == "Подходит":
            result["verdict"] = "Не подходит"
            result["reason"] = f"Недостаточно совпадений критериев ({matches}/3 минимум)"
        
        return {
            "status": "success",
            "verdict": result.get("verdict", "Не определено"),
            "reason": result.get("reason", ""),
            "matches_count": matches,
            "matched_criteria": result.get("matched_criteria", [])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "verdict": "Ошибка",
            "reason": str(e),
            "matches_count": 0,
            "matched_criteria": []
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

def generate_vacancy_profile(vacancy_title: str) -> Dict[str, Any]:
    """
    Генерирует профиль вакансии (hard/soft skills, критерии)
    
    Args:
        vacancy_title: Название вакансии (например "Python Developer")
    
    Returns:
        Dict с hard_skills, soft_skills, criteria, description
    """
    
    prompt = f"""Ты HR-эксперт. Создай профиль вакансии по названию должности.

Вакансия: {vacancy_title}

Верни СТРОГО JSON:
{{
    "hard_skills": "Python, FastAPI, PostgreSQL, Docker, Git",
    "soft_skills": "Коммуникабельность, Ответственность, Умение работать в команде",
    "description": "2-3 предложения о роли и обязанностях",
    "criteria": "Обязательно: опыт 3+ года, знание FastAPI и PostgreSQL. Желательно: опыт с Docker"
}}

Важно: hard_skills через запятую (до 10 штук), soft_skills через запятую (до 5 штук), criteria — конкретные требования для AI-анализа."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты HR-эксперт. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        return {
            "status": "success",
            "hard_skills": result.get("hard_skills", ""),
            "soft_skills": result.get("soft_skills", ""),
            "description": result.get("description", ""),
            "criteria": result.get("criteria", "")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "hard_skills": "",
            "soft_skills": "",
            "description": "",
            "criteria": ""
        }

# Экспорт функций
__all__ = ['analyze_resume', 'analyze_resume_from_hh', 'format_resume_for_analysis', 'generate_vacancy_profile']