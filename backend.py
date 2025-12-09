import os
from dotenv import load_dotenv

# СНАЧАЛА загружаем .env
load_dotenv()

# ПОТОМ импортируем остальное
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from database import db
from ai_analyzer import analyze_resume_from_hh, analyze_resume, generate_vacancy_profile
from file_parser import parse_resume_file
from fastapi import UploadFile, File, Form


app = FastAPI()

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Главная страница - наш тестовый интерфейс
@app.get("/test")
async def test_page():
    return FileResponse("static/index.html")
@app.get("/upload")
async def upload_page():
    return FileResponse("static/upload.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("static/dashboard.html")

@app.get("/vacancies")
async def vacancies_page():
    return FileResponse("static/vacancies.html")

@app.get("/settings")
async def settings_page():
    return FileResponse("static/settings.html")

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://zhenayozari-hr-assistant-bot-9ea4.twc1.net",
    "https://hr-assistant-bot-216q.onrender.com",
    "http://localhost:8000",
    "*"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Константы API
HH_API_BASE = "https://api.hh.ru"
HH_OAUTH_BASE = "https://hh.ru"

@app.get("/")
async def root():
    return {"message": "HR Assistant Backend работает!"}

# Proxy для HH.ru API
@app.api_route("/proxy/hh_api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_hh_api(path: str, request: Request):
    """Проксирует запросы к HH.ru API"""
    
    # Получаем токен из заголовка
    auth_header = request.headers.get("Authorization")
    
    # Формируем URL
    target_url = f"{HH_API_BASE}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    # Копируем заголовки
    headers = {
        "Authorization": auth_header,
        "HH-User-Agent": request.headers.get("HH-User-Agent", "HRAssistant/1.0"),
    }
    
    # Получаем тело запроса (если есть)
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.body()
    
    # Делаем запрос к HH.ru
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    
    return response.json()

# OAuth токен для HH.ru
@app.post("/proxy/hh_oauth/oauth/token")
async def get_hh_token(request: Request):
    """Обменивает authorization code на токены HH.ru"""
    
    data = await request.json()
    client_id = data.get("clientId")
    client_secret = data.get("clientSecret")
    auth_code = data.get("authCode")
    
    # Формируем запрос к HH.ru OAuth
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HH_OAUTH_BASE}/oauth/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
# === API ДЛЯ ПРОФИЛЕЙ ===

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Получить профиль пользователя"""
    profile = db.get_profile(user_id)
    if not profile:
        # Создаём новый профиль если его нет
        profile = db.create_profile(user_id)
    
    # Преобразуем telegram_chat_ids из строки в массив
    if profile.get('telegram_chat_ids'):
        try:
            profile['telegram_chat_ids'] = json.loads(profile['telegram_chat_ids'])
        except:
            profile['telegram_chat_ids'] = []
    else:
        profile['telegram_chat_ids'] = []
    
    # Преобразуем is_paid в boolean
    profile['is_paid'] = bool(profile.get('is_paid', 0))
    
    return profile

@app.put("/api/profile/{user_id}")
async def update_profile(user_id: str, request: Request):
    """Обновить профиль пользователя"""
    data = await request.json()
    
    # Если есть telegram_chat_ids, преобразуем в строку
    if 'telegram_chat_ids' in data:
        data['telegram_chat_ids'] = json.dumps(data['telegram_chat_ids'])
    
    # Если есть is_paid, преобразуем в integer
    if 'is_paid' in data:
        data['is_paid'] = 1 if data['is_paid'] else 0
    
    profile = db.update_profile(user_id, **data)
    
    # Преобразуем обратно для ответа
    if profile.get('telegram_chat_ids'):
        try:
            profile['telegram_chat_ids'] = json.loads(profile['telegram_chat_ids'])
        except:
            profile['telegram_chat_ids'] = []
    
    profile['is_paid'] = bool(profile.get('is_paid', 0))
    
    return profile

# === API ДЛЯ ВАКАНСИЙ ===

@app.post("/api/vacancies")
async def save_vacancy(request: Request):
    """Сохранить вакансию"""
    data = await request.json()
    db.save_vacancy(
        vacancy_id=data['id'],
        user_id=data['user_id'],
        title=data['title'],
        criteria=data.get('pro_talk_criteria')
    )
    return {"success": True}

@app.post("/api/vacancies/generate")
async def generate_vacancy(request: Request):
    """Генерирует описание вакансии по названию"""
    data = await request.json()
    title = data.get('title')
    
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
        
    profile = generate_vacancy_profile(title)
    return profile

@app.get("/api/vacancies/list/{user_id}")
async def get_all_vacancies(user_id: str):
    """Получить список всех вакансий"""
    return db.get_all_vacancies(user_id)

@app.get("/api/vacancies/{vacancy_id}/{user_id}")
async def get_vacancy(vacancy_id: int, user_id: str):
    """Получить вакансию"""
    vacancy = db.get_vacancy(vacancy_id, user_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return vacancy

# === API ДЛЯ КАНДИДАТОВ ===

@app.post("/api/candidates")
async def save_candidate(request: Request):
    """Сохранить кандидата"""
    data = await request.json()
    
    # Преобразуем analysis_result в строку если это объект
    analysis = data.get('analysis_result')
    if analysis and isinstance(analysis, dict):
        analysis = json.dumps(analysis)
    
    db.save_candidate(
        candidate_id=data['id'],
        user_id=data['user_id'],
        vacancy_id=data['vacancy_id'],
        full_name=data.get('full_name', ''),
        analysis_result=analysis,
        email=data.get('email'),
        phone=data.get('phone'),
        salary=data.get('salary'),
        resume_url=data.get('resume_url')
    )
    return {"success": True}

@app.get("/api/candidates/{candidate_id}/{user_id}")
async def get_candidate(candidate_id: int, user_id: str):
    """Получить кандидата"""
    candidate = db.get_candidate(candidate_id, user_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Преобразуем analysis_result обратно в объект
    if candidate.get('analysis_result'):
        try:
            candidate['analysis_result'] = json.loads(candidate['analysis_result'])
        except:
            pass
    
    return candidate

# === API ДЛЯ AI-АНАЛИЗА ===

@app.post("/api/analyze")
async def analyze_candidate(request: Request):
    """Анализировать резюме кандидата"""
    data = await request.json()
    
    full_resume = data.get('full_resume')
    criteria = data.get('criteria', '')
    
    if not full_resume:
        raise HTTPException(status_code=400, detail="full_resume is required")
    
    # Анализируем через OpenAI
    result = analyze_resume_from_hh(full_resume, criteria)
    
    return result

# === ЗАГРУЗКА РЕЗЮМЕ ===

@app.post("/api/upload_resume")
async def upload_resume(
    file: UploadFile = File(...), 
    user_id: str = Form(...),
    vacancy_id: str = Form(...)  # <--- ДОБАВИЛИ!
):
    """Загрузить, распарсить и СОХРАНИТЬ резюме С ПРИВЯЗКОЙ К ВАКАНСИИ"""
    
    # Читаем файл
    content = await file.read()
    
    # Парсим
    result = parse_resume_file(file.filename, content)
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Получаем вакансию и её критерии
    vacancy = db.get_vacancy(int(vacancy_id), user_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    criteria = vacancy.get('pro_talk_criteria') or 'Оцени кандидата'
    
    # Анализируем ПО КРИТЕРИЯМ ВАКАНСИИ
    analysis = analyze_resume(result["text"], criteria)
    
    # Сохраняем в БД
    analysis_json = json.dumps(analysis, ensure_ascii=False)
    
    import time
    new_id = int(time.time())
    
    db.save_candidate(
        candidate_id=new_id,
        user_id=user_id,
        vacancy_id=int(vacancy_id),  # <--- ПРИВЯЗКА!
        full_name=result["filename"],
        analysis_result=analysis_json,
        resume_url="local_file"
    )
    
    return {
        "filename": result["filename"],
        "text": result["text"][:500] + "...",
        "analysis": analysis
    }

# === API ДЛЯ ДАШБОРДА (НОВОЕ) ===
@app.get("/api/dashboard/stats/{user_id}")
async def get_dashboard_stats(user_id: str):
    return db.get_dashboard_stats(user_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
