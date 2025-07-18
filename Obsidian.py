import pandas as pd
from typing import Literal
import os
import re
from SIGAA import SIGAA
import ast
import json
from pathlib import Path


class Obsidian:
    def __init__(self, folder="Obsidian", gradeDF=None, historicoDF=None):
        self.folder = os.path.abspath(folder)  # Garante caminho absoluto
        self.subjects_path = os.path.join(self.folder, "Subjects")

        # Cria a pasta principal e a subpasta 'Subjects'
        os.makedirs(self.subjects_path, exist_ok=True)

        if gradeDF is None and not os.listdir(self.subjects_path):
            raise KeyError(AttributeError)

        if gradeDF is not None:
            self.perfilToMD(gradeDF)
        else:
            self.getMD()

        self.subjDF = self.getSubjectsDF()

        # Inclui Histórico no DF
        if historicoDF is not None:
            historicoDF.aprovadas = historicoDF.aprovadas.fillna("APV")
            colunas_subj = set(self.subjDF.columns)
            colunas_historico = set(historicoDF.aprovadas.T.columns)
            # Colunas exatamente iguais
            colunas_comuns = list(colunas_subj & colunas_historico)
            colunas_nao_comuns = list(colunas_historico - set(colunas_comuns))
            self.equivalencias = {}
            for col, val in self.subjDF.loc["Equivalências"].items():
                if isinstance(val, list) and val:  # está como lista com string dentro
                    try:
                        self.equivalencias[col] = val
                    except Exception as e:
                        print(
                            f"Erro ao interpretar equivalência de '{col}': {val} -> {e}"
                        )
            # Mapeia colunas não comuns para suas equivalentes
            mapa_equivalencias = {}

            for col_historico in colunas_nao_comuns:
                for col_subj, equivalentes in self.equivalencias.items():
                    if col_historico in equivalentes:
                        mapa_equivalencias[col_historico] = col_subj
                        break  # para no primeiro equivalente encontrado
            # Cria uma cópia e renomeia as colunas equivalentes
            historico_renomeado = historicoDF.aprovadas.T.rename(
                columns=mapa_equivalencias
            )

            # Atualiza lista de colunas que agora são comuns
            colunas_finais = list(
                set(self.subjDF.columns) & set(historico_renomeado.columns)
            )

            # Filtra ambos os DataFrames
            df1 = self.subjDF[colunas_finais]
            df2 = historico_renomeado[colunas_finais]

            # Concatena os DataFrames
            self.subjDF = pd.concat([self.subjDF, df2])
        self.subjDF[list(set(self.subjDF.columns) - set(df2.columns))].T.to_csv(
            "data/Faltantes.csv", encoding="utf-8"
        )
        self.dfToCanvas()

    def perfilToMD(self, excelDF):
        # Remove todos os arquivos .md antigos na pasta Subjects
        for file in os.listdir(self.subjects_path):
            if file.endswith(".md"):
                os.remove(os.path.join(self.subjects_path, file))
        self.subjects = [
            ObsidianMD(excelDF.loc[subj], how="fromExcel") for subj in excelDF.T
        ]
        self._saveMD()
        return self.subjects

    # Importa subjects dos arquivos subject.md
    def getMD(self):
        self.subjects = []
        for root, dirs, files in os.walk(self.folder):
            for file in files:
                if os.path.splitext(file)[1] == ".md":
                    self.subjects.append(
                        ObsidianMD(os.path.join(root, file), how="fromMD")
                    )
        return self.subjects

    def dfToCanvas(self):
        self.canvas = ObsidianCanvas(
            self.subjDF, folder=self.folder, subjFolder=self.subjects_path
        )

    def getSubjectsDF(self):
        subjDF = pd.DataFrame(
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
        for subject in self.subjects:
            subjDF[subject.nome] = {
                "Tipo": subject.tipo,
                "Período": subject.periodo,
                "CH Total": subject.chTotal,
                "Pré-Requisitos": subject.preReq,
                "Co-Requisitos": subject.coReq,
                "Equivalências": subject.equiv,
                "Ementa": subject.ementa,
            }
        return subjDF.fillna("")

    def _saveMD(self):
        for subject in self.subjects:
            with open(
                os.path.join(self.subjects_path, f"{subject.nome}.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(subject.MD)


class ObsidianMD(Obsidian):
    def __init__(self, subject, how: str, path=os.path.join("Obsidian", "Subjects")):
        if how == "fromMD":
            with open(path, "r", encoding="utf-8") as f:
                self.MD = f.read()
                self.nome = os.path.basename(path).replace(".md", "")
                self.mdToSubject()

        elif how == "fromExcel":
            self.nome = subject.name
            self.periodo = subject["Período"]
            self.tipo = "".join(subject["Tipo"]).replace("'", "")
            self.chTotal = subject["CH Total"]
            self.preReq = [i.replace("'", "") for i in subject["Pré-Requisitos"]]
            self.coReq = [i.replace("'", "") for i in subject["Co-Requisitos"]]
            self.equiv = [i.replace("'", "") for i in subject["Equivalências"]]
            self.ementa = "".join(subject["Ementa"]).replace("'", "")
            self.subjectToMD()

    def subjectToMD(self):
        self.MD = f"""|**Período**|**Tipo**|**CH Total**|
|-|-|-|
| {self.periodo} | {self.tipo} | {self.chTotal} |
##### Pré-Requisitos
{self._formatSubjectData(self.preReq)}
##### Có-Requisitos
{self._formatSubjectData(self.coReq)}
##### Equivalências
{self._formatSubjectData(self.equiv)}
##### Ementa
{self.ementa}
"""

    def mdToSubject(self):
        # Extract values using regular expressions
        data = {}
        header_pattern = r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
        match = re.findall(header_pattern, self.MD)
        if match:
            data["Período"], data["Tipo"], data["CH Total"] = match[-1]

        for item in ["Pré-Requisitos", "Co-Requisitos", "Equivalências"]:
            subjects_patter = f"{item}\\n(.*)?\\n"
            data[item] = re.findall(subjects_patter, self.MD)

        data["Ementa"] = re.findall(r"Ementa\n(.*)\n", self.MD)

        self.periodo = int(data["Período"])
        self.tipo = data["Tipo"]
        self.chTotal = int(data["CH Total"])
        self.preReq = self._mdFileNameToList(
            [i for i in data["Pré-Requisitos"]][0]
            if len(data["Pré-Requisitos"]) != 0
            else ""
        )
        self.coReq = self._mdFileNameToList(
            [i for i in data["Co-Requisitos"]][0]
            if len(data["Co-Requisitos"]) != 0
            else ""
        )
        self.equiv = self._mdFileNameToList(
            [i for i in data["Equivalências"]][0]
            if len(data["Equivalências"]) != 0
            else ""
        )
        self.ementa = data["Ementa"][0]

    def _mdFileNameToList(self, string):
        if string:
            pattern = r"\[\[(.*?)\]\]"
            matches = re.findall(pattern, string)
            return matches

    def _formatSubjectData(self, subjectData):
        if isinstance(subjectData, list):
            if not subjectData:
                return ""
            else:
                return str("[[" + "]], [[".join(subjectData) + "]]").replace("'", "")
                # Retorna apenas os códigos
                # codes = [data.split(" - ")[0].replace("'", "") for data in subjectData]
                # return ", ".join(f"[[{code}]]" for code in codes)
        return subjectData


class ObsidianCanvas(Obsidian):
    def __init__(
        self,
        subjDF,
        folder=f"Obsidian",
        subjFolder=os.path.join("Obsidian", "Subjects"),
    ):
        self.folder = os.path.abspath(folder)
        self.subjects_path = os.path.abspath(subjFolder)
        self.CANVAS_Y = [0] * 11
        self.Nodes = {}
        self.Edges = {}
        self.sumPreRequisitos = pd.Series(
            [self.Edges[edge]["toNode"] for edge in self.Edges]
        ).value_counts()
        self.aprovadasList = list(subjDF.loc["Média"].dropna().index)
        for subj in subjDF:
            self._setNode(subjDF[subj])
            self._setEdge(subjDF[subj])
        self._orderNode()
        self._formatEdgeColor()
        self.saveCanvas()

    def _setNode(self, subj):
        if subj["Tipo"] == "OPTATIVO":
            color = 6
        elif subj.name in self.aprovadasList:
            color = 0
        else:
            color = subj["Período"] % 2 + 4
        self.Nodes[subj.name] = {
            "id": subj.name,
            "x": 600 * subj["Período"],
            "y": self.CANVAS_Y[subj["Período"]],
            "color": color,
            "nome": subj.name.split("-")[1],
        }
        self.CANVAS_Y[subj["Período"]] += 500

    def _setEdge(self, subj):
        preReqCount = len(subj["Pré-Requisitos"])
        if preReqCount > 0:
            for preReq in subj["Pré-Requisitos"]:
                self.Edges[f'{preReq.split("-")[0]}-{subj.name.split("-")[0]}'] = {
                    "fromNode": preReq,
                    "fromSide": "right",
                    "toNode": subj.name,
                    "toSide": "left",
                    "color": 0 if preReq in self.aprovadasList else 1,
                }

    def _orderNode(self):
        for subject in self.sumPreRequisitos.keys():
            # Ordenar sumPreRequisitos em ordem decrescente
            sortedSubjects = {
                k: v
                for k, v in sorted(
                    self.sumPreRequisitos.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            }

            # Obter um conjunto de períodos únicos presentes nos nós
            periodos = set(node["x"] for node in self.Nodes.values())

            for periodo in periodos:
                # Obter todos os assuntos no período atual
                subjects_in_period = [
                    name
                    for name, details in self.Nodes.items()
                    if details["x"] == periodo
                ]

                # Criar uma série pandas com a soma dos pré-requisitos para cada assunto no período
                subjects_series = pd.Series(
                    {
                        subject: (
                            sortedSubjects[subject] if subject in sortedSubjects else 0
                        )
                        for subject in subjects_in_period
                    }
                )

                # Ordenar os assuntos por sumPreRequisitos em ordem decrescente
                subjects_in_period = subjects_series.sort_values(ascending=False).index

                for i, subject in enumerate(subjects_in_period):
                    x_coord = self.Nodes[subject]["x"]
                    y_coord = 500 * i
                    self.Nodes[subject]["y"] = y_coord

    def _formatEdgeColor(self):
        for subject in self.sumPreRequisitos.keys():
            preReqEdges = [
                chave
                for chave, edge in self.Edges.items()
                if edge["fromNode"] == subject
            ]
            for edge in preReqEdges:
                if self.Edges[edge]["color"] != 0:
                    if self.sumPreRequisitos[subject] > 2:
                        self.Edges[edge]["color"] = 1
                    elif self.sumPreRequisitos[subject] > 1:
                        self.Edges[edge]["color"] = 2
                    else:
                        self.Edges[edge]["color"] = 4

    def saveCanvas(self):
        subjectCanva = """{
        "nodes":[
                %s
            ],
        "edges":[
                %s
            ]
        }""" % (
            ",\n\t\t".join(
                [
                    ObsidianCanvas._saveNode(
                        id=self.Nodes[node]["id"],
                        x=self.Nodes[node]["x"],
                        y=self.Nodes[node]["y"],
                        color=self.Nodes[node]["color"],
                        nome=self.Nodes[node]["nome"],
                        folder=self.subjects_path,
                    )
                    for node in self.Nodes
                ]
            ),
            ",\n\t\t".join(
                [
                    self._saveEdge(
                        id=edge.replace(" ", ""),
                        fromNode=self.Edges[edge]["fromNode"],
                        fromSide=self.Edges[edge]["fromSide"],
                        toNode=self.Edges[edge]["toNode"],
                        toSide=self.Edges[edge]["toSide"],
                        color=self.Edges[edge]["color"],
                    )
                    for edge in self.Edges
                ]
            ),
        )
        with open(os.path.join(self.folder, "PE03.canvas"), "w", encoding="utf-8") as f:
            f.write(subjectCanva)
        missingCanva = """{
        "nodes":[
                %s
            ],
        "edges":[
                %s
            ]
        }""" % (
            ",\n\t\t".join(
                [
                    ObsidianCanvas._saveNode(
                        id=self.Nodes[node]["id"],
                        x=self.Nodes[node]["x"],
                        y=self.Nodes[node]["y"],
                        color=self.Nodes[node]["color"],
                        nome=self.Nodes[node]["nome"],
                        folder=self.subjects_path,
                    )
                    for node in self.Nodes
                    if node not in self.aprovadasList
                ]
            ),
            ",\n\t\t".join(
                [
                    self._saveEdge(
                        id=edge.replace(" ", ""),
                        fromNode=self.Edges[edge]["fromNode"],
                        fromSide=self.Edges[edge]["fromSide"],
                        toNode=self.Edges[edge]["toNode"],
                        toSide=self.Edges[edge]["toSide"],
                        color=self.Edges[edge]["color"],
                    )
                    for edge in self.Edges
                ]
            ),
        )
        with open(
            os.path.join(self.folder, "Faltantes.canvas"), "w", encoding="utf-8"
        ) as f:
            f.write(missingCanva)

    @staticmethod
    def _saveNode(
        id: str,
        x: int,
        y: int,
        color=0,
        nome: str = "",
        folder=os.path.join("Obsidian", "Subjects"),
    ):
        file_path = os.path.join(Path(*Path(folder).parts[-3:]), f"{id}.md").replace(
            "\\", "/"
        )
        fitID = id.split(" ")
        caracteresLinha = 0
        height = 140
        for palavra in fitID:
            tamanho_palavra = len(palavra)
            # Verifica se a palavra inteira cabe na linha atual
            if (caracteresLinha + tamanho_palavra) < 23:
                caracteresLinha += tamanho_palavra + 1  # +1 para o espaço
            else:
                # Se a palavra não couber, começa uma nova linha
                height += 40
                caracteresLinha = tamanho_palavra + 1  # +1 para o espaço

        return f'{{"id":"{id}","type":"file","file":"{file_path}","width":440,"height":{height},"color":"{color}","x":{x},"y":{y}}}'

    @staticmethod
    def _saveEdge(
        id: str,
        fromNode: str,
        fromSide: Literal["top", "bottom", "left", "right"],
        toNode: str,
        toSide: Literal["top", "bottom", "left", "right"],
        color=0,
    ):
        return f'{{"id":"{id}","fromNode":"{fromNode}","fromSide":"{fromSide}","toNode":"{toNode}","toSide":"{toSide}","color":"{color}"}}'


if __name__ == "__main__":
    if os.path.exists("data/myData.json"):
        wait_password = False
        with open("data/myData.json", "r", encoding="utf-8") as f:
            path = json.load(f)["Obsidian_path"]
            f.close()
    siga = SIGAA()
    if path != "":
        obsidian = Obsidian(
            gradeDF=siga.curriculo.df, historicoDF=siga.historico, folder=path
        )
    else:
        obsidian = Obsidian(gradeDF=siga.curriculo.df, historicoDF=siga.historico)

    ...
