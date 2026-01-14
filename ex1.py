

import re
import os
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from PyPDF2 import PdfReader
import warnings

warnings.filterwarnings('ignore')


# Базовый набор стоп-слов (служебные слова, не несущие смысловой нагрузки)
STOP_WORDS = {
  
    'и', 'а', 'но', 'или', 'да', 'же', 'ли', 'то', 'не', 'ни',
    'в', 'во', 'на', 'по', 'под', 'над', 'от', 'до', 'за', 'из',
    'у', 'к', 'ко', 'с', 'со', 'о', 'об', 'про', 'для', 'при',
    'так', 'как', 'что', 'когда', 'где', 'чем', 'если', 'же',
    'это', 'этот', 'эта', 'эти', 'тот', 'та', 'те', 'такой', 'такая', 'такие',
    # Дополнительные русские служебные / малозначимые в частотном анализе
    'после', 'перед', 'между', 'надо', 'около', 'рядом',
    'затем', 'потом', 'далее', 'также', 'тоже', 'поэтому',
    'однако', 'например', 'впрочем', 'почти', 'уже', 'еще',
    'снова', 'опять', 'тогда', 'сейчас', 'здесь', 'туда', 'сюда',
    'там', 'тут', 'поэтому', 'кроме', 'вместе', 'всегда', 'часто',
    'редко', 'обычно', 'иногда', 'весь', 'вся', 'всё', 'все',
    'сам', 'сама', 'само', 'сами', 'другой', 'другая', 'другие', 'этом',
    # Русские местоимения
    'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они',
    'меня', 'тебя', 'его', 'ее', 'нас', 'вас', 'их',
    'мой', 'моя', 'мое', 'мои',
    'твой', 'твоя', 'твое', 'твои',
    'наш', 'наша', 'наше', 'наши',
    'ваш', 'ваша', 'ваше', 'ваши',
    'свой', 'своя', 'свое', 'свои',
    # Частые служебные/технические куски в русских текстах
    'рис', 'табл', 'стр',
    # Английские
    'the', 'a', 'an', 'of', 'in', 'on', 'at', 'for', 'to', 'from',
    'with', 'by', 'and', 'or', 'but', 'as', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'that', 'this', 'these',
    'those', 'it', 'its', 'into', 'about', 'over', 'under',
    'between', 'among', 'up', 'down', 'out', 'off', 'than',
    'then', 'so', 'such', 'not', 'no', 'nor', 'very',
    # Английские местоимения
    'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'her', 'our', 'their',
    'mine', 'yours', 'ours', 'theirs', 'hers',
    'myself', 'yourself', 'himself', 'herself', 'itself',
    'ourselves', 'yourselves', 'themselves',
    # Языковые маркеры
    'ru', 'eng', 'англ',  'doi', 'org', 'https', 'http', 'www', 'url', 'abs', 'summarization'
}

# Настройка для корректного отображения русского текста
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class TextFrequencyAnalyzer:
    """Класс для частотного анализа текста в PDF/TXT файлах"""
    
    def __init__(self, pdf_path):
    
        self.pdf_path: str = pdf_path
        self.filename: str = os.path.basename(pdf_path)
        self.text: str = ""
        self.words: list[str] = []
        self.frequency_dict: dict[str, int] = {}
        self.sorted_frequencies: list[tuple[str, int]] = []
        
  

    def _ensure_output_dir(self, output_dir: str) -> str:
        """Гарантирует существование директории для сохранения результатов"""
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _get_base_output_name(self) -> str:
        """Базовое имя файла без расширения для формирования имён отчётов"""
        return os.path.splitext(self.filename)[0]

    def _get_top_words(self, top_n: int):
        """Возвращает списки слов и их частот для топ-N по убыванию"""
        top_words = self.sorted_frequencies[:top_n]
        words = [item[0] for item in top_words]
        freqs = [item[1] for item in top_words]
        return words, freqs



    def load_text(self):
        """Извлечение текста из файла (PDF или TXT)"""
        try:
            # Определяем тип файла по расширению
            file_ext = os.path.splitext(self.pdf_path)[1].lower()
            
            if file_ext == '.pdf':
                # Чтение PDF файла
                reader = PdfReader(self.pdf_path)
                extracted_text = ""
                for page in reader.pages:
                    extracted_text += (page.extract_text() or "") + " "
                self.text = extracted_text
            elif file_ext == '.txt':
                # Чтение текстового файла
                with open(self.pdf_path, 'r', encoding='utf-8') as f:
                    self.text = f.read()
            else:
                print(f"[ОШИБКА] Неподдерживаемый формат файла: {file_ext}")
                return False
            
            return True
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            try:
                with open(self.pdf_path, 'r', encoding='cp1251') as f:
                    self.text = f.read()
                print(f"[OK] Текст извлечен из {self.filename} (кодировка cp1251)")
                return True
            except Exception as e:
                print(f"[ОШИБКА] Не удалось прочитать файл {self.filename}: {e}")
                return False
        except Exception as e:
            print(f"[ОШИБКА] Неожиданная ошибка при чтении {self.filename}: {e}")
            return False
    
    def tokenize_text(self):
        """Предобработка текста: токенизация и нормализация"""
        # Приведение к нижнему регистру
        text_lower = self.text.lower()
        
        # Извлечение слов (кириллица и латиница)
        # Используем регулярное выражение для поиска слов
        raw_tokens = re.findall(r'\b[а-яёa-z]+\b', text_lower, re.IGNORECASE)
        
        # Фильтрация:
        # 1) убираем слова короче 2 символов
        # 2) убираем русские/английские стоп-слова (предлоги, союзы и т.п.)
        self.words = [
            token for token in raw_tokens
            if len(token) >= 2 and token not in STOP_WORDS
        ]
        
    
    def build_frequency_map(self):
        """Построение частотного словаря"""
        self.frequency_dict = Counter(self.words)
        
        # Сортировка по убыванию частоты
        self.sorted_frequencies = sorted(
            self.frequency_dict.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
    
    def compute_statistics(self):
        """Вычисление основных частотных характеристик"""
        total_words = len(self.words)
        unique_words = len(self.frequency_dict)
        
        # Частоты
        frequencies = list(self.frequency_dict.values())
        
        # Основные статистики
        stats_summary = {
            'Общее количество слов': total_words,
            'Количество уникальных слов': unique_words,
            'Средняя частота слова': np.mean(frequencies),
            'Медианная частота': np.median(frequencies),
            'Максимальная частота': np.max(frequencies),
            'Минимальная частота': np.min(frequencies),
            'Стандартное отклонение': np.std(frequencies),
            'Коэффициент вариации': np.std(frequencies) / np.mean(frequencies) if np.mean(frequencies) > 0 else 0,
            'Слово с максимальной частотой': self.sorted_frequencies[0][0] if self.sorted_frequencies else '',
            'Частота самого частого слова': self.sorted_frequencies[0][1] if self.sorted_frequencies else 0
        }
        
        return stats_summary
    
    def export_frequency_report(self, output_dir='Результаты анализа'):
        """Сохранение частотного словаря в файл"""
        self._ensure_output_dir(output_dir)
        
        # Создаем имя файла без расширения
        base_name = self._get_base_output_name()
        # Сохраняем с понятной "припиской" в имени файла
        output_file = os.path.join(output_dir, f'{base_name}_частотный_словарь.txt')
        
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(f"{'Слово':<30} {'Абс. частота':<15} {'Отн. частота, %':<20}\n")
            
            total_words = len(self.words)
            for word, freq in self.sorted_frequencies:
                rel_freq = (freq / total_words) * 100 if total_words > 0 else 0
                output.write(f"{word:<30} {freq:<15} {rel_freq:>10.4f}\n")
        
    
    def plot_step_function(self, output_dir='Результаты анализа', top_n=50):
        """Построение графика ступенчатой функции распределения частот"""
        self._ensure_output_dir(output_dir)
        
        # Берем топ-N слов по частоте
        words, frequencies = self._get_top_words(top_n)
        
        plt.figure(figsize=(14, 8))
        plt.step(range(len(frequencies)), frequencies, where='post', linewidth=2)
        plt.xlabel('Порядковый номер слова (по убыванию частоты)', fontsize=12)
        plt.ylabel('Частота', fontsize=12)
        plt.title(f'Ступенчатая функция распределения частот\n{self.filename}', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.xticks(range(0, len(frequencies), max(1, len(frequencies)//10)))
        
        base_name = self._get_base_output_name()
        output_file = os.path.join(output_dir, f'{base_name}_ступенчатая_функция.png')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    
    def plot_frequency_distribution(self, output_dir='Результаты анализа', top_n=30):
        """Построение графика распределения частот слов"""
        self._ensure_output_dir(output_dir)
        
        # Берем топ-N слов
        words, frequencies = self._get_top_words(top_n)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(words)), frequencies, color='steelblue', alpha=0.7)
        plt.xlabel('Слова', fontsize=12)
        plt.ylabel('Частота', fontsize=12)
        plt.title(f'Распределение частот слов (топ-{top_n})\n{self.filename}', fontsize=14, fontweight='bold')
        plt.xticks(range(len(words)), words, rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Добавляем значения на столбцы
        for i, (bar, freq) in enumerate(zip(bars, frequencies)):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{freq}', ha='center', va='bottom', fontsize=9)
        
        base_name = self._get_base_output_name()
        output_file = os.path.join(output_dir, f'{base_name}_распределение_частот.png')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    
    def plot_frequency_rank(self, output_dir='Результаты анализа', top_n=100):
        """Построение графика зависимости частоты от ранга (закон Ципфа)"""
        self._ensure_output_dir(output_dir)
        
        # Берем топ-N слов
        _, frequencies = self._get_top_words(top_n)
        ranks = range(1, len(frequencies) + 1)
        
        plt.figure(figsize=(12, 8))
        plt.loglog(ranks, frequencies, 'o-', markersize=4, linewidth=1.5)
        plt.xlabel('Ранг слова (log)', fontsize=12)
        plt.ylabel('Частота (log)', fontsize=12)
        plt.title(f'Зависимость частоты от ранга (закон Ципфа)\n{self.filename}', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, which='both')
        
        base_name = self._get_base_output_name()
        output_file = os.path.join(output_dir, f'{base_name}_закон_ципфа.png')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    
    def save_statistics_table(self, stats, output_dir='Результаты анализа'):
        """Сохранение таблицы со сводной статистикой"""
        self._ensure_output_dir(output_dir)
        
        base_name = self._get_base_output_name()
        output_file = os.path.join(output_dir, f'{base_name}_статистика.txt')
        
        with open(output_file, 'w', encoding='utf-8') as output:
            
            for metric_name, metric_value in stats.items():
                if isinstance(metric_value, float):
                    output.write(f"{metric_name:<40}: {metric_value:>12.4f}\n")
                else:
                    output.write(f"{metric_name:<40}: {metric_value}\n")
        
    
    def analyze(self):
        """Запускает полный анализ одного текстового файла и сохраняет
        все результаты в отдельную подпапку внутри 'Результаты анализа'."""

        # Извлечение текста
        if not self.load_text():
            return False

        # Предобработка
        self.tokenize_text()

        # Построение частотного словаря
        self.build_frequency_map()

        # Вычисление статистики
        stats = self.compute_statistics()

        # Базовая папка для всех результатов по этому файлу
        base_results_dir = os.path.join("Результаты анализа", self._get_base_output_name())

        # Сохранение результатов в эту подпапку
        self.export_frequency_report(output_dir=base_results_dir)
        self.save_statistics_table(stats, output_dir=base_results_dir)

        # Построение графиков в ту же подпапку
        self.plot_step_function(output_dir=base_results_dir)
        self.plot_frequency_distribution(output_dir=base_results_dir)
        self.plot_frequency_rank(output_dir=base_results_dir)

        return True


def _collect_source_files(directory: str = ".", max_files: int = 4):
    """Возвращает список TXT-файлов для анализа (не более max_files штук)"""
    txt_files = [
        file_name
        for file_name in os.listdir(directory)
        if file_name.lower().endswith('.txt')
    ]
    if len(txt_files) > max_files:
        txt_files = txt_files[:max_files]
    return txt_files




def _print_program_footer() -> None:
    """Выводит финальное сообщение по окончании работы программы"""
    print("\n" + "-" * 30)
    print("Анализ файлов завершен")
    print("Все результаты работы будут сохранены в папке - 'Результаты анализа' ")
    print("-" * 30)


def main():
    """Точка входа в программу"""

    source_files = _collect_source_files()

    if not source_files:
        print("[ОШИБКА] Не найдено ни одного TXT файла для анализа в текущей директории.")
        return
    
    print("Будут обработаны следующие файлы:")
    for file_name in source_files:
        print(f"  {file_name}")
    
    # Анализ каждого файла отдельно
    for source_path in source_files:
        if not os.path.exists(source_path):
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Файл не найден и будет пропущен: {source_path}")
            continue
        analyzer_instance = TextFrequencyAnalyzer(source_path)
        analyzer_instance.analyze()
    
    _print_program_footer()


if __name__ == "__main__":
    main()
