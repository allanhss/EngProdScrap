from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import openpyxl
import re


class Historico:
    def __init__(self, historico):
        self.df = historico
        self.aprovadas = historico.loc[
            historico["Situação"].isin(["APROVADO POR MÉDIA", "DISPENSADO"]), ["Média"]
        ]


class PerfilCurricular:
    def __init__(self, perfilCurricular):
        self.df = perfilCurricular.applymap(
            lambda x: [i for i in x.strip("[]").replace("", "").split(", ") if i != ""]
            if isinstance(x, str)
            else x
        )


class SIGAA:
    def __init__(self):
        self._SIGAAON = False
        self.historico = self.GetHistorico()
        self.curriculo = self.GetCurriculo()

    def _SIGAA_Init(self):
        self.driver = webdriver.Chrome(options=Options().add_argument("--incognito"))
        self.driver.get("https://www.siga.univasf.edu.br/univasf/")
        self.driver.implicitly_wait(0.5)

        # Login
        if self.driver.title == "SIG@UNIVASF":
            try:
                while 1:
                    # Esperar o usuário entrar CPF/Senha
                    self.driver.find_element(by=By.ID, value="cpf")
                    self.driver.implicitly_wait(1)
            except:
                self._SIGAAON = True
                print("Login OK")

    def _SIGAA_FindCurriculo(self, grade="PRO03", how="Bloco"):
        # Find Curriculo
        self.driver.implicitly_wait(5)
        self.driver.switch_to.default_content()
        self.driver.find_element(
            by=By.ID, value="menuTopo:repeatAcessoMenu:0:linkDescricaoMenu"
        ).click()
        self.driver.find_element(
            by=By.ID,
            value="menuTopo:repeatAcessoMenu:0:repeatSuperTransacoesSuperMenu:0:linkSuperTransacaoSuperMenu",
        ).click()
        self.driver.implicitly_wait(5)

        # Consultar Perfis Curriculares do Curso
        self.driver.switch_to.frame("Conteudo")

        selectCurso = Select(
            self.driver.find_element(by=By.ID, value="codigoProgramaFormacao")
        )
        selectCurso.select_by_visible_text("ENGENHARIA DE PRODUÇÃO")
        self.driver.implicitly_wait(5)

        self.driver.switch_to.frame("idIFrameComboPerfil")
        selectGrade = Select(
            self.driver.find_element(by=By.ID, value="codigoPerfilSelect")
        )
        selectGrade.select_by_visible_text(grade)

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("Conteudo")

        selectCod = self.driver.find_element(by=By.NAME, value="codPerfil")

        self.driver.find_elements(by=By.CSS_SELECTOR, value="font.edit")
        self.driver.find_elements(by=By.NAME, value="ordenacao")[
            {"Bloco": 0, "Período": 1}[how]
        ].click()

        for btn in self.driver.find_elements(by=By.CLASS_NAME, value="botao"):
            if btn.accessible_name == "Consultar":
                btn.click()
        print("Consulta OK")

    def GetCurriculo(self, grade="PRO03"):
        try:
            return PerfilCurricular(pd.read_excel(f"data\{grade}.xlsx", index_col=0))

        except FileNotFoundError:
            print("Curriculo Not Found")
            if not self._SIGAAON:
                self._SIGAA_Init()

            self._SIGAA_FindCurriculo(grade, how="Bloco")
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("Conteudo")

            # Perfil Curricular
            consulta = self.driver.find_element(
                by=By.XPATH, value='//*[@id="form-corpo"]'
            )
            soup = BeautifulSoup(consulta.get_attribute("outerHTML"), "html.parser")
            consultaDiv = soup.find(id="form-corpo")

            ## CICLO GERAL
            cicloBasicoRaw = consultaDiv.find(
                id="CICLO GERAL OU CICLO BÁSICO 0"
            ).find_all("tr")
            perfil = self._SearchRawBlock(cicloBasicoRaw)
            print("CICLO GERAL OK")

            # CICLO PROFISSIONAL
            cicloProfissionalRaw = consultaDiv.find(
                id="CICLO PROFISSIONAL OU TRONCO COMUM 29"
            ).find_all("tr")
            perfil = perfil.join(self._SearchRawBlock(cicloProfissionalRaw))
            print("CICLO PROFISSIONAL OK")

            # CICLO OPTATIVO
            cicloOptativoRaw = consultaDiv.find(
                id="COMPONENTES OPTATIVOS  - DISCIPLINAS OPTATIVAS63"
            ).find_all("tr")
            perfil = perfil.join(self._SearchRawBlock(cicloOptativoRaw))
            print("OPTATIVAS OK")

            PerfilFull = perfil.sort_values(
                ["Período", "Tipo"], axis="columns", ascending=True
            ).T
            PerfilFull.to_excel(f"data\{grade}.xlsx")
            print(f"Curriculo {grade} OK")
            return PerfilCurricular(PerfilFull)

    def GetHistorico(self, file="data\Historico.xlsx"):
        try:
            return Historico(pd.read_excel(file, index_col=0))

        except FileNotFoundError:
            print("Historico not Found")
            # Menu -> Detalhamento do Discente
            if not self._SIGAAON:
                self._SIGAA_Init()
            self.driver.implicitly_wait(5)
            self.driver.switch_to.default_content()
            self.driver.find_element(
                by=By.ID, value="menuTopo:repeatAcessoMenu:1:linkDescricaoMenu"
            ).click()
            self.driver.find_element(
                by=By.ID,
                value="menuTopo:repeatAcessoMenu:1:repeatSuperTransacoesSuperMenu:0:linkSuperTransacaoSuperMenu",
            ).click()
            self.driver.implicitly_wait(5)

            # Menu Sec -> Histórico
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("Conteudo")
            self.driver.implicitly_wait(5)
            self.driver.find_element(
                By.ID, value="form:repeatTransacoes:1:outputPanelTransacoes"
            ).click()

            # Histórico
            self.driver.switch_to.default_content()
            self.driver.implicitly_wait(5)
            self.driver.switch_to.frame("Conteudo")

            consulta = self.driver.find_element(
                by=By.XPATH, value='//*[@id="form-corpo"]'
            )
            soup = BeautifulSoup(consulta.get_attribute("outerHTML"), "html.parser")
            consultaDiv = soup.find(id="form-corpo")
            self.driver.implicitly_wait(5)

            histSubjects = [
                [td.get_text(strip=True) for td in i.find_previous("tr").find_all("td")]
                for dataTable in consultaDiv.find_all("table")
                for i in dataTable.find_all("tr")
                if " - " in (i.get("id") or "")
            ]
            histFull = pd.DataFrame(
                histSubjects,
                columns=[
                    "Componente Curricular",
                    "Faltas",
                    "CH",
                    "Créditos",
                    "Média",
                    "Situação",
                ],
            )
            histFull.to_excel(file, index=False)
            print("Histórico OK")
            return Historico(histFull)

    def _StringCleaner(self, string):
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

    def _SearchRawSubject(self, subjectRawData, headerData):
        subject = {}
        subject["Nome"] = (
            subjectRawData[0][headerData.index("Componente Curricular")]
            .partition("COLEGIADO")[0]
            .partition("COORDENAÇÃO")[0]
        )
        subject["Tipo"] = subjectRawData[0][headerData.index("Tipo")]
        subject["Período"] = int(subjectRawData[0][headerData.index("Período")])
        subject["CH Total"] = int(subjectRawData[0][headerData.index("CH Total")])
        for data in subjectRawData[1:]:
            if "Pré-Requisitos" in data:
                if "Não exist" in data[1]:
                    subject["Pré-Requisitos"] = []
                    preReqON = False
                else:
                    subject["Pré-Requisitos"] = []
                    preReqON = True
            elif "Co-Requisitos" in data:
                preReqON = False
                if "Não exist" in data[1]:
                    subject["Co-Requisitos"] = []
                    CoreqON = False
                else:
                    subject["Co-Requisitos"] = []
                    CoreqON = True

            elif "Requisito Carga Horária" in data:
                CoreqON = False
                continue
            elif "Equivalências" in data:
                if "Não exist" in data[1]:
                    subject["Equivalências"] = [""]
                    equivalON = False
                else:
                    subject["Equivalências"] = []
                    equivalON = True
            elif "Ementa" in data:
                equivalON = False
                subject["Ementa"] = (
                    subjectRawData[subjectRawData.index(["Ementa"]) + 1]
                    if ["Ementa"] in subjectRawData
                    else []
                )

            elif data != []:
                for item in data:
                    parts = re.findall(
                        r"[A-Z]+\d+\s+-\s+.*?(?=(?:[A-Z]+\d+\s+-|$))", item
                    )
                    for point in parts:
                        if preReqON:
                            if point not in subject["Pré-Requisitos"]:
                                subject["Pré-Requisitos"].append(point)
                        elif CoreqON:
                            if point not in subject["Co-Requisitos"]:
                                subject["Co-Requisitos"].append(point)
                        elif equivalON:
                            if point not in subject["Equivalências"]:
                                subject["Equivalências"].append(point)
        return subject

    def _SearchRawBlock(self, subjectRawBlock):
        # Get all "font"
        fontList = [
            [
                self._StringCleaner(value.get_text())
                for value in row.find_all(
                    "font",
                )
            ]
            for row in subjectRawBlock
        ]

        # Get Header Names
        for elem in fontList:
            if "Componente Curricular" in elem:
                headerIndex = fontList.index(elem)
                break
        headerData = fontList[headerIndex]

        # Find all Subjects Index using header Size
        subjectsIndexList = [
            fontList.index(i)
            for i in fontList[headerIndex + 1 :]
            if len(i) == len(fontList[headerIndex])
        ]
        subjectsIndexList.append(len(fontList))  # Get last Subject

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
            subjectRawData = fontList[subjectsIndexList[i] : subjectsIndexList[i + 1]]
            subject = self._SearchRawSubject(subjectRawData, headerData)
            subjects[subject["Nome"]] = subject
        return subjects


if __name__ == "__main__":
    siga = SIGAA()
    print(siga.historico.aprovadas)
    print(siga.curriculo.df)
