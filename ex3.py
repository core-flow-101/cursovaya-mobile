import re
import os

class NameIndexIndexer:
    """Класс для построения именного указателя"""

    def __init__(self, filepath='test.txt'):
        self.filepath = filepath
        self.text = ""
        self.personalities = set()
        self.toponyms = set()
        self.companies = set()
        self.software_products = set()
        self.abbreviations = set()

    # -------------------- Загрузка текста --------------------
    def load_text(self):
        """Загрузка текста из файла с поддержкой utf-8 и cp1251"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.text = f.read()
        except UnicodeDecodeError:
            with open(self.filepath, 'r', encoding='cp1251') as f:
                self.text = f.read()
        

    # -------------------- Универсальные методы --------------------
    def _add_matches_to_set(self, patterns, target_set, min_len=3, ignore_words=None):
        """Ищет все совпадения по паттернам и добавляет в target_set"""
        ignore_words = ignore_words or []
        for pattern in patterns:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                match = match.strip()
                if match and len(match) >= min_len and not any(word in match.lower() for word in ignore_words):
                    target_set.add(match)

    def _add_known_items(self, known_list, target_set):
        """Добавляет известные элементы, если они встречаются в тексте"""
        for item in known_list:
            if item in self.text or item.lower() in self.text.lower():
                target_set.add(item)

    # -------------------- Извлечение элементов --------------------
    def extract_personalities(self):
        """Извлечение персоналий"""
        patterns = [
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b',  # Имя Отчество Фамилия
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.',               # Фамилия И.О.
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]{3,}\b',                # Имя Фамилия
            r'\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]{3,}\b'           # И.О. Фамилия
        ]
        self._add_matches_to_set(patterns, self.personalities, ignore_words=['глава', 'раздел', 'параграф', 'страница'])
        

    def extract_toponyms(self):
        """Извлечение топонимов"""
        patterns = [
            r'\b[А-ЯЁ][а-яё]*(?:град|город|ск|инск|енск|анск|онск|ия|стан|бург|поль)\b',
            r'\b[А-ЯЁ][а-яё]{4,}\b'
        ]
        known_toponyms = [
            'Москва', 'Санкт-Петербург', 'Россия', 'США', 'Европа',
            'Азия', 'Америка', 'Африка', 'Англия', 'Франция', 'Германия'
        ]
        self._add_matches_to_set(patterns, self.toponyms)
        self._add_known_items(known_toponyms, self.toponyms)
        # Исключаем персоналии
        self.toponyms -= self.personalities
       

    def extract_companies(self):
        """Извлечение компаний"""
        patterns = [
            r'(?:ООО|ЗАО|ОАО|ПАО|ИП|Ltd|Inc|Corp|LLC)\s+["«]?([А-ЯЁA-Z][^"»\n]{2,30})["»]?',
            r'["«]([А-ЯЁA-Z][^"»\n]{5,40})["»]',
            r'\b(?:компания|фирма|корпорация|группа)\s+["«]?([А-ЯЁA-Z][^"»\n]{2,30})["»]?'
        ]
        self._add_matches_to_set(patterns, self.companies)
        

    def extract_software_products(self):
        """Извлечение программных продуктов"""
        patterns = [
            r'\b([А-ЯЁA-Z][а-яёa-z]+\s+\d+\.?\d*)\b',
            r'\b(?:система|программа|пакет|платформа|фреймворк|библиотека)\s+["«]?([А-ЯЁA-Z][^"»\n]{2,30})["»]?',
            r'\b(?:Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|Haskell|Lisp|Prolog|SQL|HTML|CSS|XML|JSON|YAML|Git|Linux|Windows|macOS|Android|iOS|Django|Flask|React|Vue|Angular|TensorFlow|PyTorch|NumPy|Pandas|Matplotlib|Scikit-learn|NLTK|spaCy)\b'
        ]
        known_software = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby',
            'Windows', 'Linux', 'macOS', 'Android', 'iOS',
            'Django', 'Flask', 'React', 'Vue', 'Angular',
            'TensorFlow', 'PyTorch', 'NumPy', 'Pandas'
        ]
        self._add_matches_to_set(patterns, self.software_products)
        self._add_known_items(known_software, self.software_products)
       

    def extract_abbreviations(self):
        """Извлечение аббревиатур"""
        patterns = [r'\b[А-ЯЁA-Z]{2,6}\b']
        self._add_matches_to_set(patterns, self.abbreviations)
        

    # -------------------- Построение и сохранение --------------------
    def build_index(self):
        """Полное построение именного указателя"""
        self.load_text()
        self.extract_personalities()
        self.extract_toponyms()
        self.extract_companies()
        self.extract_software_products()
        self.extract_abbreviations()
        return {
            'personalities': self.personalities,
            'toponyms': self.toponyms,
            'companies': self.companies,
            'software_products': self.software_products,
            'abbreviations': self.abbreviations
        }

    def save_index(self, output_dir='Результаты анализа'):
        """Сохранение именного указателя в текстовый файл"""
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        output_file = os.path.join(output_dir, f'{base_name}_name_index.txt')

        sections = [
            ('ПЕРСОНАЛИИ', self.personalities),
            ('ТОПОНИМЫ', self.toponyms),
            ('КОМПАНИИ', self.companies),
            ('ПРОГРАММНЫЕ ПРОДУКТЫ', self.software_products),
            ('АББРЕВИАТУРЫ', self.abbreviations)
        ]

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ИМЕННОЙ УКАЗАТЕЛЬ\n" + "="*60 + "\n\n")
            total_count = 0
            for title, items in sections:
                f.write(f"{title}\n" + "-"*60 + "\n")
                for i, item in enumerate(sorted(items), 1):
                    f.write(f"{i}. {item}\n")
                f.write(f"\nВсего {title.lower()}: {len(items)}\n\n")
                total_count += len(items)
            f.write("="*60 + "\n")
            f.write(f"ОБЩЕЕ КОЛИЧЕСТВО: {total_count}\n")
            f.write("="*60 + "\n")
        


def main():
    text_files = [f for f in os.listdir('.') if f.lower().endswith('.txt')]
    if not text_files:
        print("[WARN] Нет TXT файлов для обработки!")
        return

    # Ограничение до 4 файлов
    text_files = text_files[:4]

    for file_path in text_files:
        
        indexer = NameIndexIndexer(file_path)
        indexer.build_index()
        indexer.save_index()

    
if __name__ == "__main__":
    main()
