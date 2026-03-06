from flask import Flask, render_template, request, session, jsonify
import requests
import json
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
import csv
import os
import threading
import queue
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it'  # Измените на свой ключ

# Хранилище для долгих запросов
search_results = {}
search_status = {}


class HHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_vacancies(self, text: str, area: str = None, pages: int = 3, progress_queue=None) -> List[Dict]:
        """Поиск вакансий с возможностью отслеживания прогресса"""
        all_vacancies = []
        
        # Получаем ID региона если указан
        area_id = None
        if area:
            area_id = self._get_area_id(area)
        
        params = {
            'text': text,
            'per_page': 100,
            'page': 0
        }
        
        if area_id:
            params['area'] = area_id
        
        for page in range(pages):
            params['page'] = page
            
            if progress_queue:
                progress_queue.put({'type': 'page', 'page': page + 1, 'total_pages': pages})
            
            try:
                response = self.session.get(f"{self.base_url}vacancies", params=params)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    break
                
                # Получаем детальную информацию по каждой вакансии
                for i, vacancy in enumerate(vacancies, 1):
                    if progress_queue:
                        progress_queue.put({
                            'type': 'vacancy', 
                            'page': page + 1,
                            'current': i, 
                            'total': len(vacancies)
                        })
                    
                    full_vacancy = self._get_vacancy_details(vacancy['id'])
                    if full_vacancy:
                        processed_vacancy = self._process_vacancy(full_vacancy)
                        all_vacancies.append(processed_vacancy)
                    time.sleep(0.2)
                
                if len(vacancies) < 100:
                    break
                    
            except Exception as e:
                print(f"Ошибка при загрузке страницы {page + 1}: {e}")
                if progress_queue:
                    progress_queue.put({'type': 'error', 'message': str(e)})
                break
        
        return all_vacancies
    
    def _get_area_id(self, area_name: str) -> int:
        """Получение ID региона по названию"""
        try:
            response = self.session.get(f"{self.base_url}areas")
            response.raise_for_status()
            areas = response.json()
            return self._find_area_id(areas, area_name)
        except:
            return None
    
    def _find_area_id(self, areas: List, area_name: str) -> int:
        """Рекурсивный поиск ID региона"""
        for area in areas:
            if area['name'].lower() == area_name.lower():
                return area['id']
            if area.get('areas'):
                result = self._find_area_id(area['areas'], area_name)
                if result:
                    return result
        return None
    
    def _get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        try:
            response = self.session.get(f"{self.base_url}vacancies/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def _process_vacancy(self, vacancy: Dict) -> Dict:
        """Обработка вакансии и извлечение нужных полей"""
        return {
            'name': self._extract_contact_name(vacancy),
            'phone': self._extract_phone(vacancy),
            'speciality': self._get_speciality(vacancy),
            'salary': self._format_salary(vacancy.get('salary')),
            'region': self._get_region(vacancy),
            'company': self._get_company(vacancy),
            'url': self._get_url(vacancy),
            'date': self._get_date(vacancy)
        }
    
    def _extract_contact_name(self, vacancy: Dict) -> str:
        """Извлечение имени контактного лица"""
        contacts = vacancy.get('contacts')
        if contacts and isinstance(contacts, dict):
            if contacts.get('name'):
                return contacts.get('name')
        
        description = vacancy.get('description', '')
        if description:
            name_patterns = [
                r'Контактное лицо:?\s*([А-Я][а-я]+\s+[А-Я][а-я]+)',
                r'Контакт:?\s*([А-Я][а-я]+\s+[А-Я][а-я]+)',
                r'HR:\s*([А-Я][а-я]+\s+[А-Я][а-я]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, description)
                if match:
                    return match.group(1)
        
        return "Не указано"
    
    def _extract_phone(self, vacancy: Dict) -> str:
        """Извлечение телефона из вакансии"""
        contacts = vacancy.get('contacts')
        if contacts and isinstance(contacts, dict):
            phones = contacts.get('phones')
            if phones and isinstance(phones, list) and len(phones) > 0:
                phone = phones[0]
                if isinstance(phone, dict):
                    country = phone.get('country', '')
                    city = phone.get('city', '')
                    number = phone.get('number', '')
                    
                    if country and city and number:
                        return f"+{country}{city}{number}"
                    elif number:
                        return number
        
        description = vacancy.get('description', '')
        if description:
            phone_patterns = [
                r'(\+7|8)[\s(.-]?(\d{3})[\s).-]?(\d{3})[\s.-]?(\d{2})[\s.-]?(\d{2})',
                r'(\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, description)
                if match:
                    return match.group(0)
        
        return "Не указан"
    
    def _format_salary(self, salary: Optional[Dict]) -> str:
        """Форматирование зарплаты"""
        if not salary or not isinstance(salary, dict):
            return "Не указана"
        
        salary_from = salary.get('from')
        salary_to = salary.get('to')
        currency = salary.get('currency', 'руб.')
        
        if salary_from and salary_to:
            return f"{salary_from} - {salary_to} {currency}"
        elif salary_from:
            return f"от {salary_from} {currency}"
        elif salary_to:
            return f"до {salary_to} {currency}"
        else:
            return "Не указана"
    
    def _get_region(self, vacancy: Dict) -> str:
        """Получение региона"""
        area = vacancy.get('area')
        if area and isinstance(area, dict):
            return area.get('name', 'Не указан')
        return "Не указан"
    
    def _get_speciality(self, vacancy: Dict) -> str:
        """Получение специальности"""
        return vacancy.get('name', 'Не указана')
    
    def _get_company(self, vacancy: Dict) -> str:
        """Получение названия компании"""
        employer = vacancy.get('employer')
        if employer and isinstance(employer, dict):
            return employer.get('name', 'Не указана')
        return "Не указана"
    
    def _get_url(self, vacancy: Dict) -> str:
        """Получение ссылки на вакансию"""
        return vacancy.get('alternate_url', '')
    
    def _get_date(self, vacancy: Dict) -> str:
        """Получение даты публикации"""
        published = vacancy.get('published_at')
        if published:
            return published[:10]
        return "Не указана"


def async_search(search_id, query, region, pages):
    """Асинхронный поиск вакансий"""
    parser = HHParser()
    progress_queue = queue.Queue()
    
    search_status[search_id] = {
        'status': 'in_progress',
        'progress': 0,
        'message': 'Начинаем поиск...',
        'queue': progress_queue
    }
    
    try:
        results = parser.search_vacancies(
            text=query,
            area=region if region else None,
            pages=pages,
            progress_queue=progress_queue
        )
        
        search_results[search_id] = results
        search_status[search_id]['status'] = 'completed'
        search_status[search_id]['message'] = f'Найдено {len(results)} вакансий'
        
    except Exception as e:
        search_status[search_id]['status'] = 'error'
        search_status[search_id]['message'] = str(e)


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/contacts')
def contacts():
    """Страница с контактами"""
    return render_template('contacts.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Страница поиска"""
    if request.method == 'POST':
        query = request.form.get('query', '')
        region = request.form.get('region', '')
        pages = int(request.form.get('pages', 3))
        
        # Сохраняем параметры в сессии
        session['last_query'] = query
        session['last_region'] = region
        session['last_pages'] = pages
        
        # Запускаем асинхронный поиск
        import uuid
        search_id = str(uuid.uuid4())
        
        thread = threading.Thread(
            target=async_search,
            args=(search_id, query, region, pages)
        )
        thread.daemon = True
        thread.start()
        
        return render_template('search.html', 
                             search_started=True,
                             search_id=search_id,
                             query=query,
                             region=region,
                             pages=pages)
    
    # GET запрос - показываем форму
    return render_template('search.html',
                         last_query=session.get('last_query', ''),
                         last_region=session.get('last_region', ''),
                         last_pages=session.get('last_pages', 3))


@app.route('/search_status/<search_id>')
def get_search_status(search_id):
    """Получение статуса поиска"""
    if search_id in search_status:
        status = search_status[search_id].copy()
        # Удаляем очередь из статуса перед отправкой
        if 'queue' in status:
            del status['queue']
        return jsonify(status)
    return jsonify({'status': 'not_found'})


@app.route('/search_results/<search_id>')
def get_search_results(search_id):
    """Получение результатов поиска"""
    if search_id in search_results:
        return jsonify({
            'status': 'success',
            'results': search_results[search_id]
        })
    return jsonify({'status': 'not_found'})


@app.route('/check_timeout', methods=['POST'])
def check_timeout():
    """Проверка таймаута и запрос продолжения"""
    data = request.json
    search_id = data.get('search_id')
    
    if search_id in search_status:
        # Спрашиваем пользователя
        return jsonify({
            'timeout': True,
            'message': 'Поиск длится более 5 минут. Продолжить?'
        })
    
    return jsonify({'timeout': False})


@app.route('/continue_search', methods=['POST'])
def continue_search():
    """Продолжение поиска после подтверждения"""
    data = request.json
    search_id = data.get('search_id')
    continue_search = data.get('continue', False)
    
    if search_id in search_status:
        search_status[search_id]['continue'] = continue_search
        return jsonify({'success': True})
    
    return jsonify({'success': False})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)