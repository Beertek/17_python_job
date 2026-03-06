import requests
import json
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
import csv
import os


class HHParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_vacancies(self, text: str, area: str = None, pages: int = 3) -> List[Dict]:
        """
        Поиск вакансий по заданным параметрам с указанных страниц
        """
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
            
            try:
                response = self.session.get(f"{self.base_url}vacancies", params=params)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    break
                
                print(f"Страница {page + 1}: найдено {len(vacancies)} вакансий")
                
                # Получаем детальную информацию по каждой вакансии
                for vacancy in vacancies:
                    full_vacancy = self._get_vacancy_details(vacancy['id'])
                    if full_vacancy:
                        all_vacancies.append(full_vacancy)
                    time.sleep(0.2)
                
                if len(vacancies) < 100:
                    break
                    
            except Exception as e:
                print(f"Ошибка при загрузке страницы {page + 1}: {e}")
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
    
    def extract_contact_name(self, vacancy: Dict) -> str:
        """Извлечение имени контактного лица"""
        # Пробуем получить из контактов
        contacts = vacancy.get('contacts')
        if contacts and isinstance(contacts, dict):
            if contacts.get('name'):
                return contacts.get('name')
        
        # Пробуем найти имя в описании
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
    
    def extract_phone(self, vacancy: Dict) -> str:
        """Извлечение телефона из вакансии"""
        # Пробуем получить из контактов API
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
        
        # Пробуем найти телефон в описании
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
    
    def format_salary(self, salary: Optional[Dict]) -> str:
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
    
    def get_region(self, vacancy: Dict) -> str:
        """Получение региона"""
        area = vacancy.get('area')
        if area and isinstance(area, dict):
            return area.get('name', 'Не указан')
        return "Не указан"
    
    def get_speciality(self, vacancy: Dict) -> str:
        """Получение специальности"""
        return vacancy.get('name', 'Не указана')
    
    def get_company(self, vacancy: Dict) -> str:
        """Получение названия компании"""
        employer = vacancy.get('employer')
        if employer and isinstance(employer, dict):
            return employer.get('name', 'Не указана')
        return "Не указана"
    
    def get_url(self, vacancy: Dict) -> str:
        """Получение ссылки на вакансию"""
        return vacancy.get('alternate_url', '')
    
    def get_date(self, vacancy: Dict) -> str:
        """Получение даты публикации"""
        published = vacancy.get('published_at')
        if published:
            return published[:10]
        return "Не указана"


class VacancyCollector:
    def __init__(self):
        self.parser = HHParser()
        self.results = []
    
    def collect_vacancies(self, search_query: str, area: str = None, pages: int = 3) -> List[Dict]:
        """
        Сбор вакансий и формирование таблицы с результатами
        """
        print(f"\nПоиск: {search_query}")
        print(f"Регион: {area if area else 'вся Россия'}")
        print(f"Страниц: {pages}\n")
        
        # Получаем вакансии
        vacancies = self.parser.search_vacancies(
            text=search_query,
            area=area,
            pages=pages
        )
        
        print(f"\nОбработка вакансий...")
        
        # Формируем строки для таблицы
        for vacancy in vacancies:
            row = {
                'Имя': self.parser.extract_contact_name(vacancy),
                'Телефон': self.parser.extract_phone(vacancy),
                'Специальность': self.parser.get_speciality(vacancy),
                'Зарплата': self.parser.format_salary(vacancy.get('salary')),
                'Регион': self.parser.get_region(vacancy),
                'Компания': self.parser.get_company(vacancy),
                'Ссылка': self.parser.get_url(vacancy),
                'Дата': self.parser.get_date(vacancy)
            }
            
            self.results.append(row)
        
        print(f"Всего обработано: {len(self.results)} вакансий\n")
        return self.results
    
    def print_table(self, limit: int = 10):
        """
        Вывод таблицы с результатами
        """
        if not self.results:
            print("Нет данных для отображения")
            return
        
        # Заголовки
        headers = ['Имя', 'Телефон', 'Специальность', 'Зарплата', 'Регион', 'Компания']
        
        # Определяем ширину колонок
        col_widths = [len(h) for h in headers]
        for row in self.results[:limit]:
            for i, key in enumerate(['Имя', 'Телефон', 'Специальность', 'Зарплата', 'Регион', 'Компания']):
                col_widths[i] = max(col_widths[i], len(str(row.get(key, ''))[:30]))
        
        # Ограничиваем ширину
        col_widths = [min(w, 30) for w in col_widths]
        
        # Разделитель
        separator = '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'
        
        # Заголовок
        print(separator)
        header_row = '|'
        for i, header in enumerate(headers):
            header_row += f" {header:<{col_widths[i]}} |"
        print(header_row)
        print(separator)
        
        # Данные
        for row in self.results[:limit]:
            data_row = '|'
            for i, key in enumerate(['Имя', 'Телефон', 'Специальность', 'Зарплата', 'Регион', 'Компания']):
                value = str(row.get(key, ''))
                if len(value) > col_widths[i]:
                    value = value[:col_widths[i]-3] + '...'
                data_row += f" {value:<{col_widths[i]}} |"
            print(data_row)
        
        print(separator)
        
        if len(self.results) > limit:
            print(f"\n... и ещё {len(self.results) - limit} записей")
    
    def save_to_csv(self, filename: str = None):
        """
        Сохранение результатов в CSV файл
        """
        if not self.results:
            print("Нет данных для сохранения")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vacancies_{timestamp}.csv"
        
        fieldnames = ['Имя', 'Телефон', 'Специальность', 'Зарплата', 'Регион', 'Компания', 'Ссылка', 'Дата']
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\nРезультаты сохранены в файл: {filename}")
        print(f"Всего записей: {len(self.results)}")
    
    def get_statistics(self):
        """Получение статистики"""
        if not self.results:
            return
        
        total = len(self.results)
        with_phones = sum(1 for r in self.results if r['Телефон'] != 'Не указан')
        with_names = sum(1 for r in self.results if r['Имя'] != 'Не указано')
        with_salary = sum(1 for r in self.results if r['Зарплата'] != 'Не указана')
        
        print("\n" + "="*50)
        print("СТАТИСТИКА")
        print("="*50)
        print(f"Всего вакансий: {total}")
        print(f"С телефоном: {with_phones} ({with_phones/total*100:.1f}%)")
        print(f"С контактным лицом: {with_names} ({with_names/total*100:.1f}%)")
        print(f"С зарплатой: {with_salary} ({with_salary/total*100:.1f}%)")


def main():
    """Основная функция"""
    print("Программа для сбора вакансий с hh.ru")
    print("-" * 40)
    
    search_query = input("Введите поисковый запрос: ").strip()
    if not search_query:
        search_query = "рабочий"
        print(f"Используется запрос: {search_query}")
    
    region = input("Введите регион (Enter - вся Россия): ").strip()
    if not region:
        region = None
    
    pages = input("Введите количество страниц (Enter - 3): ").strip()
    try:
        pages = int(pages) if pages else 3
    except ValueError:
        pages = 3
    
    collector = VacancyCollector()
    
    # Сбор вакансий
    collector.collect_vacancies(
        search_query=search_query,
        area=region,
        pages=pages
    )
    
    # Вывод таблицы
    collector.print_table(limit=15)
    
    # Статистика
    collector.get_statistics()
    
    # Сохранение
    collector.save_to_csv()
    
    print("\nГотово!")


if __name__ == "__main__":
    main()