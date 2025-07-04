import os
import pdfplumber
import json
import re


def extrair_turmas_pdf(caminho_pdf):
    turmas = []
    turma_atual = {}
    professores = []
    horarios = []

    with pdfplumber.open(caminho_pdf) as pdf:
        texto_completo = ""
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    # Quebra por blocos iniciados por "TURMA"
    blocos = re.split(r"\nTURMA ", texto_completo)
    for bloco in blocos[1:]:  # ignora o primeiro que não é turma
        linhas = bloco.strip().splitlines()

        # Primeira linha: turma e vagas
        linha_0 = linhas[0]
        turma_info = linha_0.strip().split(maxsplit=1)
        turma = turma_info[0]
        vagas = int(re.findall(r"\d+", turma_info[1])[0])

        # Segunda linha: componente
        componente = linhas[1].strip()

        # Busca por professores
        idx_prof = linhas.index("PROFESSOR (ES)") + 1
        professores = []
        while linhas[idx_prof] and not linhas[idx_prof].startswith("DIA DA SEMANA"):
            nome = linhas[idx_prof].replace("*", "").strip()
            if nome.upper() != "NÃO INFORMADO" and nome.upper() != "NÃO INFORMADA":
                professores.append(nome)
            idx_prof += 1

        # Busca por carga horária
        carga_horaria_match = re.search(r"(\d+)", linhas[idx_prof])
        carga_horaria = (
            int(carga_horaria_match.group()) if carga_horaria_match else None
        )

        # Coleta os horários
        horarios = []
        for linha in linhas[idx_prof + 1 :]:
            if not linha.strip():
                continue
            partes = linha.strip().split()
            if len(partes) >= 3:
                dia = partes[0]
                sala = partes[1]
                hs = partes[2:]
                horarios.append({"dia": dia, "sala": sala, "horarios": hs})
            else:
                break  # chega ao final da seção

        turma_dict = {
            "turma": turma,
            "vagas": vagas,
            "componente": componente,
            "professores": professores,
            "carga_horaria": carga_horaria,
            "horarios": horarios,
        }

        turmas.append(turma_dict)

    return turmas


files = [
    os.path.join("data", "Ofertas 2025.2", file)
    for file in os.listdir("data\Ofertas 2025.2")
]


# Extração
dados_turmas = extrair_turmas_pdf(files[0])

# Exporta para JSON (opcional)
with open("test\turmas_2025_2.json", "w", encoding="utf-8") as f:
    json.dump(dados_turmas, f, ensure_ascii=False, indent=2)
