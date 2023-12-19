from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup, NavigableString
import pandas as pd


def StringCleaner(string):
    return (
        string.replace("\n", "")
        .replace("\t", "")
        .replace(";", "")
        .replace("\xa0", "")
        .replace("º", "")
        .replace("*", "")
        .replace(":", "")
        .replace(".", "")
    )


def SearchRawSubject(subjectRawData, strInit):
    return [
        split_subject
        for subject in [
            subj[1]
            for subj in subjectRawData
            if strInit in subj and "Não exist" not in subj[1]
        ]
        for split_subject in subject.replace("Fórmula", "")
        .replace("OU", "")
        .replace(" E ", " ")
        .split(" ")
        if split_subject != ""
    ]


def SearchRawBlock(subjectRawBlock):
    blockList = [
        [
            StringCleaner(value.get_text())
            for value in row.find_all(
                "font",
            )
        ]
        for row in subjectRawBlock
    ]

    # Get Header ID
    for elem in blockList:
        if "Componente Curricular" in elem:
            header_ID = blockList.index(elem)
            break
    headerData = blockList[header_ID]

    # Find all Subjects
    subjectsIndexList = [
        blockList.index(i)
        for i in blockList[header_ID + 1 :]
        if len(i) == len(blockList[header_ID])
    ]
    subjectsIndexList.append(len(blockList))  # Get last Subject
    subjects = pd.DataFrame(
        index=[
            "Tipo",
            "Período",
            "CH Total",
            "Pré-Requisitos",
            "Co-Requisitos",
            "Equivalências",
            "Ementa",
        ]
    )

    for i in range(len(subjectsIndexList) - 1):
        subjectRawData = blockList[subjectsIndexList[i] : subjectsIndexList[i + 1]]
        subjects[
            subjectRawData[0][headerData.index("Componente Curricular")]
            .partition("COLEGIADO")[0]
            .partition("COORDENAÇÃO")[0]
        ] = [
            subjectRawData[0][headerData.index("Tipo")],
            int(subjectRawData[0][headerData.index("Período")]),
            int(subjectRawData[0][headerData.index("CH Total")]),
            SearchRawSubject(subjectRawData, "Pré-Requisitos"),
            SearchRawSubject(subjectRawData, "Co-Requisitos"),
            SearchRawSubject(subjectRawData, "Equivalências"),
            subjectRawData[subjectRawData.index(["Ementa"]) + 1]
            if ["Ementa"] in subjectRawData
            else [],
        ]
    return subjects


driver = webdriver.Chrome()
driver.get("https://www.siga.univasf.edu.br/univasf/")
driver.implicitly_wait(0.5)

# Login
if driver.title == "SIG@UNIVASF":
    try:
        while 1:
            # Esperar o usuário entrar CPF/Senha
            driver.find_element(by=By.ID, value="cpf")
            driver.implicitly_wait(5)
    except:
        print("Login OK")

# Find Curriculo
menuTopo = driver.find_elements(by=By.CLASS_NAME, value="menu-link")
for child in menuTopo:
    if child.text == "Currículo":
        child.click()
        driver.implicitly_wait(5)
        driver.find_element(
            by=By.XPATH, value="//*[text()='Perfis Curriculares do Curso']"
        ).click()

# Consultar Perfis Curriculares do Curso
driver.switch_to.frame("Conteudo")

selectCurso = Select(driver.find_element(by=By.ID, value="codigoProgramaFormacao"))
selectCurso.select_by_visible_text("ENGENHARIA DE PRODUÇÃO")
driver.implicitly_wait(5)

driver.switch_to.frame("idIFrameComboPerfil")
selectCurso = Select(driver.find_element(by=By.ID, value="codigoPerfilSelect"))
selectCurso.select_by_visible_text("PRO03")

driver.switch_to.default_content()
driver.switch_to.frame("Conteudo")

selectCod = driver.find_element(by=By.NAME, value="codPerfil")


driver.find_elements(by=By.CSS_SELECTOR, value="font.edit")
# 0= Bloco     1= Período
driver.find_elements(by=By.NAME, value="ordenacao")[0].click()

for btn in driver.find_elements(by=By.CLASS_NAME, value="botao"):
    if btn.accessible_name == "Consultar":
        btn.click()
print("Consulta OK")

driver.switch_to.default_content()
driver.switch_to.frame("Conteudo")

# Perfil Curricular
consulta = driver.find_element(by=By.XPATH, value='//*[@id="form-corpo"]')
soup = BeautifulSoup(consulta.get_attribute("outerHTML"), "html.parser")
consultaDiv = soup.find(id="form-corpo")

## CICLO GERAL
cicloBasicoRaw = consultaDiv.find(id="CICLO GERAL OU CICLO BÁSICO 0").find_all("tr")
PerfilCurricular = SearchRawBlock(cicloBasicoRaw)
print("CICLO GERAL OK")

# CICLO PROFISSIONAL
cicloProfissional = consultaDiv.find(
    id="CICLO PROFISSIONAL OU TRONCO COMUM 29"
).find_all("tr")
PerfilCurricular = PerfilCurricular.join(SearchRawBlock(cicloProfissional))
print("CICLO PROFISSIONAL OK")

# CICLO OPTATIVO
cicloOptativo = consultaDiv.find(
    id="COMPONENTES OPTATIVOS  - DISCIPLINAS OPTATIVAS63"
).find_all("tr")
PerfilCurricular = PerfilCurricular.join(SearchRawBlock(cicloOptativo))
print("OPTATIVAS OK")


PerfilCurricular.sort_values(
    ["Período", "Tipo"], axis="columns", ascending=True
).T.to_excel("PRO03.xlsx")
print("Plano de Matérias OK")
#########################################################
...
# Menu -> Detalhamento do Discente
driver.switch_to.default_content()
driver.find_element(
    by=By.ID, value="menuTopo:repeatAcessoMenu:1:linkDescricaoMenu"
).click()
driver.find_element(
    by=By.ID,
    value="menuTopo:repeatAcessoMenu:1:repeatSuperTransacoesSuperMenu:0:linkSuperTransacaoSuperMenu",
).click()

# Menu Sec -> Histórico
driver.switch_to.default_content()
driver.switch_to.frame("Conteudo")
driver.find_element(
    By.ID, value="form:repeatTransacoes:1:outputPanelTransacoes"
).click()

# Histórico
driver.switch_to.default_content()
driver.switch_to.frame("Conteudo")

consulta = driver.find_element(by=By.XPATH, value='//*[@id="form-corpo"]')
soup = BeautifulSoup(consulta.get_attribute("outerHTML"), "html.parser")
consultaDiv = soup.find(id="form-corpo")

histSubjects = [
    [td.get_text(strip=True) for td in i.find_previous("tr").find_all("td")]
    for dataTable in consultaDiv.find_all("table")
    for i in dataTable.find_all("tr")
    if " - " in (i.get("id") or "")
]
pd.DataFrame(
    histSubjects,
    columns=["Componente Curricular", "Faltas", "CH", "Créditos", "Média", "Situação"],
).to_excel("Historico.xlsx", index=False)
print("Histórico OK")
