import os
import pandas as pd
from prettytable import PrettyTable
import chardet

class PriceListAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.data = []  # Общий список данных из всех файлов
        self.name_columns = ["название", "продукт", "товар", "наименование"]
        self.price_columns = ["цена", "розница"]
        self.weight_columns = ["фасовка", "масса", "вес"]

    def _detect_encoding_and_delimiter(self, file_path):
        """
        Определяет кодировку и разделитель файла.
        """
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)
        encoding = chardet.detect(raw_data)['encoding']

        with open(file_path, encoding=encoding) as file:
            first_line = file.readline()
            delimiter = ';' if ';' in first_line else ','

        return encoding, delimiter

    def load_prices(self):
        """
        Сканирует папку и загружает данные из файлов с именем, содержащим "price".
        """
        processed_files = 0
        failed_files = 0
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if "price" in file.lower() and file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    try:
                        print(f"Проверка файла: {file}")
                        encoding, delimiter = self._detect_encoding_and_delimiter(file_path)
                        df = pd.read_csv(file_path, sep=delimiter, encoding=encoding, 
                                         engine='python', skip_blank_lines=True, on_bad_lines='skip')
                        
                        df.columns = df.columns.str.lower().str.strip()
                        df = self._extract_relevant_columns(df)
                        df["файл"] = file
                        self.data.append(df)
                        processed_files += 1
                    except Exception as e:
                        print(f"Ошибка при обработке файла {file}: {e}")
                        failed_files += 1
        if not self.data:
            raise ValueError("Не удалось загрузить ни одного корректного файла. Проверьте структуру данных.")
        self.data = pd.concat(self.data, ignore_index=True)
        self.data = self.data.sort_values(by="цена за кг", ascending=True).reset_index(drop=True)
        print(f"Загружено файлов: {processed_files}, Ошибок: {failed_files}")

    def _extract_relevant_columns(self, df):
        """
        Извлекает и переименовывает нужные столбцы (название, цена, вес).
        """
        name_col = self._find_column(df, self.name_columns)
        price_col = self._find_column(df, self.price_columns)
        weight_col = self._find_column(df, self.weight_columns)

        if not (name_col and price_col and weight_col):
            raise ValueError("Не найдены все обязательные столбцы: название, цена, вес")

        df = df[[name_col, price_col, weight_col]].copy()
        df.columns = ["название", "цена", "вес"]
        df["цена за кг"] = df["цена"] / df["вес"]
        return df

    def _find_column(self, df, possible_names):
        """
        Ищет столбец по возможным названиям.
        """
        for col in possible_names:
            if col in df.columns:
                return col
        return None

    def find_text(self, text):
        """
        Возвращает список позиций с сортировкой по цене за килограмм, содержащих фрагмент текста.
        """
        result = self.data[self.data["название"].str.contains(text, case=False, na=False)].copy()
        result = result.sort_values(by="цена за кг", ascending=True)
        table = PrettyTable(["#", "Наименование", "Цена", "Вес", "Файл", "Цена за кг"])
        for idx, row in enumerate(result.itertuples(), 1):
            table.add_row([idx, row.название, row.цена, row.вес, row.файл, round(row._5, 2)])
        print(table)

    def export_to_html(self, output_file="output.html"):
        """
        Экспортирует все данные в HTML-файл.
        """
        self.data.to_html(output_file, index=False)
        print(f"Данные успешно экспортированы в {output_file}")


# Пример использования
if __name__ == "__main__":
    folder_path = "./Практическое задание _Анализатор прайс-листов._"  # Путь к папке с файлами
    analyzer = PriceListAnalyzer(folder_path)
    try:
        analyzer.load_prices()
        while True:
            user_input = input("Введите текст для поиска (или 'exit' для выхода): ")
            if user_input.lower() == 'exit':
                print("Работа завершена.")
                break
            analyzer.find_text(user_input)
        # Экспорт данных в HTML
        analyzer.export_to_html()
    except ValueError as e:
        print(e)
