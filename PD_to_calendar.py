import pdfplumber
from pdfminer.layout import LAParams
import re
import glob
import pandas as pd

# Definindo parâmetros ajustados para a extração de texto
laparams = LAParams(
    line_overlap=0.5,
    char_margin=2.0,
    line_margin=0.5,
    word_margin=0.1,
    boxes_flow=0.5
)

pattern = re.compile(
    r'^(?=.*Data)(?=.*Conteúdo)(?=.*Horário)(?=.*Qtd de Aulas)(?=.*Professor Responsável).+$',
    re.IGNORECASE
)

def extract_info_from_pdf(pdf_path):
    # Coleta o conteúdo de todas as páginas
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(laparams=laparams)
            if text:
                print(f"[DEBUG] Página {i} de {pdf_path}:\n{text[:200]}...\n")
                full_text += text + "\n"
            else:
                print(f"[DEBUG] Página {i} de {pdf_path} sem texto extraído.")
    
    # Busca a linha que contém os cabeçalhos desejados
    lines = full_text.splitlines()
    for idx, line in enumerate(lines):
        if pattern.match(line):
            print(f"[DEBUG] Linha identificada: {line.strip()}")
            print("[DEBUG] Linhas seguintes:")
            for subsequent_line in lines[idx+1:]:
                print(subsequent_line)
            break

    # Extrair informações com os novos padrões
    period_match = re.search(r"PERÍODO LETIVO:\s*([\d\.]+)", full_text, re.IGNORECASE)
    ofertante_match = re.search(r"OFERTANTE:\s*(.+)", full_text, re.IGNORECASE)
    disciplina_match = re.search(r"Disciplina\s+(.+)", full_text, re.IGNORECASE)
    
    return {
        "Arquivo": pdf_path,
        "Período": period_match.group(1).strip() if period_match else None,
        "Ofertante": ofertante_match.group(1).strip() if ofertante_match else None,
        "Disciplina": disciplina_match.group(1).strip() if disciplina_match else None
    }

# Define o diretório dos arquivos PDF e coleta todos os PDFs
pdf_dir = "data/2025.1/PDs"  # novo path
pdf_files = glob.glob(f"{pdf_dir}/*.pdf")  # listagem dos arquivos pdf
print(f"[DEBUG] PDFs encontrados: {len(pdf_files)} -> {pdf_files}")

all_results = []
for pdf_path in pdf_files:
    print(f"\nExtraindo dados de {pdf_path}:")
    result = extract_info_from_pdf(pdf_path)
    all_results.append(result)

# Cria um DataFrame com os dados extraídos e os imprime
df = pd.DataFrame(all_results)
print("\nDataframe com todos os dados processados:")
print(df)