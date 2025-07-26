import sys
import os
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import re
import traceback

def extract_data_with_ocr(pdf_path):
    """
    Convierte un PDF a imágenes, realiza OCR en cada imagen y extrae
    los datos de la tabla utilizando expresiones regulares.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo '{pdf_path}' no fue encontrado.")
        return

    print("Iniciando extracción con OCR (puede tardar unos minutos)...")

    try:
        # 1. Convertir el PDF a una lista de imágenes
        print("Paso 1/3: Convirtiendo PDF a imágenes...")
        images = convert_from_path(pdf_path)

        all_rows = []
        
        # 2. Definir la expresión regular para capturar las columnas
        # Este patrón está diseñado específicamente para el formato de tu tabla
        # Captura 8 grupos: Item, Description, NCM, Unit, Quantity, R1, R2, Amount
        regex_pattern = re.compile(
            r"^\s*(\d{2})\s+"                    # Grupo 1: Item (2 dígitos al inicio)
            r"(.+?)\s+"                         # Grupo 2: Description (cualquier caracter, no codicioso)
            r"(\d{4}\.\d{2}\.\d{2})\s+"          # Grupo 3: NCM (formato XXXX.XX.XX)
            r"([A-Z]{2,3})\s+"                  # Grupo 4: Unit (2 o 3 letras mayúsculas)
            r"([\d\.,]+(?:\.\d{2})?)\s+"         # Grupo 5: Quantity (números, puntos, comas)
            r"([\d\.,]+)\s+"                    # Grupo 6: R1
            r"([\d\.,]+)\s+"                    # Grupo 7: R2
            r"([\d\.,]+)\s*$"                   # Grupo 8: Amount (al final de la línea)
        )

        print("Paso 2/3: Realizando OCR en cada página...")
        for i, image in enumerate(images):
            print(f"  - Procesando página {i + 1}...")
            # Extraer todo el texto de la imagen, especificando el idioma portugués
            text = pytesseract.image_to_string(image, lang='por')
            
            # 3. Procesar el texto línea por línea
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                match = regex_pattern.search(line)
                if match:
                    # Si la línea coincide con nuestro patrón de tabla, extraemos los datos
                    all_rows.append(list(match.groups()))

        if not all_rows:
            print("Error: No se pudieron extraer filas de datos con OCR. Verifica la calidad del PDF o el patrón de regex.")
            return

        print("Paso 3/3: Creando el archivo CSV...")
        # Crear un DataFrame de pandas con los datos extraídos
        column_names = ['Item', 'DISCRIPTION', 'NCM', 'Unit', 'Quantity', 'R1', 'R2', 'Amount']
        df = pd.DataFrame(all_rows, columns=column_names)

        # Guardar el DataFrame en un archivo CSV
        output_csv_path = os.path.splitext(pdf_path)[0] + '_ocr_result.csv'
        df.to_csv(output_csv_path, index=False, encoding='utf-8')

        print(f"\n¡Éxito! Los datos han sido extraídos con OCR y guardados en: '{output_csv_path}'")

    except Exception as e:
        print(f"\nOcurrió un error inesperado durante el proceso de OCR: {e}")
        print("Posibles causas:")
        print("- ¿Están Tesseract y Poppler instalados y en el PATH del sistema?")
        print("- ¿Se instaló el paquete de idioma portugués para Tesseract (`tesseract-ocr-por`)?")
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("Uso: python ocr_extractor.py <ruta_al_archivo.pdf>")
        sys.exit(1)
    extract_data_with_ocr(sys.argv[1])

if __name__ == '__main__':
    main()
