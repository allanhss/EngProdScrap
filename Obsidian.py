import pandas as pd
from typing import Literal
import os
import re
import paths
from SIGAA import SIGAA


class Obsidian:
    def __init__(self, folder, *gradeDF):
        self.folder = folder
        if not os.path.exists(self.folder):
            # Cria diretório caso não exista
            os.makedirs(self.folder)
            if not gradeDF:
                raise KeyError(AttributeError)
            self.perfilToMD(gradeDF)
        elif not gradeDF:
            self.getMD()
        self.subjDF = self.getSubjectsDF()

    # Cria subject.md a partir da grade no Excel
    def perfilToMD(self, excelDF):
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

    def saveCanvas(self):
        for subject in self.subjects:
            ObsidianCanvas(subject)

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
            with open(f"{self.folder}\\{subject.nome}.md", "w", encoding="utf-8") as f:
                f.write(subject.MD)


class ObsidianMD(Obsidian):
    def __init__(self, subject, how: str):
        if how == "fromMD":
            with open(subject, "r", encoding="utf-8") as f:
                self.MD = f.read()
                self.nome = subject.split("\\")[-1].replace(".md", "")
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
    def __init__(self):
        self.CANVAS_Y = [0] * 11
        self.Nodes = pd.DataFrame(index=["color", "x", "y", "nome"])
        self.Edges = pd.DataFrame(
            index=["fromNode", "fromSide", "toNode", "toSide", "color"]
        )

    def _SetNode(id: str, x: int, y: int, color=0, nome: str = ""):
        if len(nome) < 25:
            height = 220
        elif len(nome) < 50:
            height = 260
        else:
            height = 300
        return f'{{"id":"{id}","type":"file","file":"PlanoMaterias/Subjects/{id}.md","width":440,"height":{height},"color":"{color}","x":{x},"y":{y}}}'

    def _SetEdge(
        self,
        id: str,
        fromNode: str,
        fromSide: Literal["top", "bottom", "left", "right"],
        toNode: str,
        toSide: Literal["top", "bottom", "left", "right"],
        color=0,
    ):
        return f'{{"id":"{id}","fromNode":"{fromNode}","fromSide":"{fromSide}","toNode":"{toNode}","toSide":"{toSide}","toEnd":"none","color":"{color}"}}'

    def SubjectToCANVAS(self, subjectDF):
        CODIGO, NOME, *_ = subjectDF.name.split(" - ")
        PERIODO = int(subjectDF["Período"])
        TIPO = "".join(subjectDF["Tipo"]).replace("'", "")
        preRequisitos = [i.replace("'", "") for i in subjectDF["Pré-Requisitos"]]
        coRequisitos = [i.replace("'", "") for i in subjectDF["Co-Requisitos"]]
        equivalencias = [i.replace("'", "") for i in subjectDF["Equivalências"]]
        if CODIGO in aprovadas:
            color = 0
        elif TIPO == "OPTATIVO":
            color = 6
        else:
            color = PERIODO % 2 + 4
        self.Nodes[CODIGO] = [
            color,
            600 * PERIODO,
            self.CANVAS_Y[PERIODO],
            NOME,
        ]
        self.CANVAS_Y[PERIODO] += 500

        for preReq in preRequisitos:
            self.Edges[f"{CODIGO}-{preReq}"] = [
                CODIGO,
                "left",
                preReq,
                "right",
                0 if preReq in aprovadas else 1,
            ]

    def OrganizeCANVAS(self):
        # Set Color by Needed
        sumPreRequisitos = pd.Series(
            [self.Edges[edge]["toNode"] for edge in self.Edges]
        ).value_counts()

        for subject in sumPreRequisitos.keys():
            selectedSubjects = [
                self.Edges[edge].name
                for edge in self.Edges
                if self.Edges[edge]["toNode"] == subject
            ]
            for edge in selectedSubjects:
                if self.Edges[edge]["color"] != 0:
                    if sumPreRequisitos[subject] > 2:
                        self.Edges[edge]["color"] = 1
                    elif sumPreRequisitos[subject] > 1:
                        self.Edges[edge]["color"] = 2
                    else:
                        self.Edges[edge]["color"] = 4
            print("self.Edges ajustadas")

            # Order Y by sumPreRequisitos
            sortedSubjects = sumPreRequisitos.sort_values(ascending=False)
            periodos = self.Nodes.loc["x"].unique()

            for periodo in periodos:
                subjects_in_period = self.Nodes.columns[self.Nodes.loc["x"] == periodo]
                subjects_series = pd.Series(
                    {
                        subject: sortedSubjects[subject]
                        if subject in sortedSubjects
                        else 0
                        for subject in subjects_in_period
                    }
                )
                subjects_in_period = subjects_series.sort_values(ascending=False).index

                for i, subject in enumerate(subjects_in_period):
                    x_coord = self.Nodes.loc["x", subject]
                    y_coord = 500 * i
                    self.Nodes.loc["y", subject] = y_coord
            print("self.Nodes reordenados")

    def SaveCANVAS(self):
        subjectCanva = """{
            "self.nodes":[
                %s
            ],
            "self.edges":[
                %s
            ]
        }""" % (
            ",\n\t\t".join(
                [
                    self._SetNode(
                        id=self.Nodes[node].name,
                        x=self.Nodes[node]["x"],
                        y=self.Nodes[node]["y"],
                        color=self.Nodes[node]["color"],
                        nome=self.Nodes[node]["nome"],
                    )
                    for node in self.Nodes
                ]
            ),
            ",\n\t\t".join(
                [
                    self._SetEdge(
                        id=self.Edges[edge].name,
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
        with open(f"{self.folder}PR03.canvas", "w", encoding="utf-8") as f:
            f.write(subjectCanva)


if __name__ == "__main__":
    siga = SIGAA()
    aprovadas = siga.historico.aprovadas
    PerfilCurricular = siga.curriculo.df
    print("Grade Processada")

    obsidian = Obsidian(
        folder=paths.ObsidianFolder
        if hasattr(paths, "ObsidianFolder")
        else f"Obsidian\\",
        gradeDF=PerfilCurricular,
    )

    ...
