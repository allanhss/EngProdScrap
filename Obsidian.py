import pandas as pd
from typing import Literal
import os
import re
import paths
from SIGAA import SIGAA


class Obsidian:
    def __init__(self, folder=f"Obsidian\\", gradeDF=None, historicoDF=None):
        self.folder = folder
        if not os.path.exists(self.folder):
            # Cria diretório caso não exista
            os.makedirs(self.folder)
            os.makedirs(f"{self.folder}Subjects")
            if gradeDF is None:
                raise KeyError(AttributeError)
            self.perfilToMD(gradeDF)
        elif gradeDF is None:
            self.getMD()
        else:
            self.perfilToMD(gradeDF)
        self.subjDF = self.getSubjectsDF()

        # Inclui Histórico no DF
        if historicoDF is not None:
            self.subjDF = pd.concat(
                [self.subjDF, historicoDF.aprovadas.T.fillna("APV")]
            ).fillna("")

        self.dfToCanvas()

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

    def dfToCanvas(self):
        self.canvas = ObsidianCanvas(self.subjDF, folder=self.folder)

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
                f"{self.folder}Subjects\\{subject.nome}.md", "w", encoding="utf-8"
            ) as f:
                f.write(subject.MD)


class ObsidianMD(Obsidian):
    def __init__(self, subject, how: str, path=f"Obsidian\\Subjects"):
        if how == "fromMD":
            with open(path, "r", encoding="utf-8") as f:
                self.MD = f.read()
                self.nome = path.split("\\")[-1].replace(".md", "")
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
    def __init__(self, subjDF, folder=f"Obsidian"):
        self.folder = folder
        self.CANVAS_Y = [0] * 11
        self.Nodes = {}
        self.Edges = {}

        for subj in subjDF:
            self._setNode(subjDF[subj])
            self._setEdge(subjDF[subj])

        self.saveCanvas()

    def _setNode(self, subj):
        if subj["Tipo"] == "OPTATIVO":
            color = 6
        elif subj["Média"] != None:
            color = 0
        else:
            color = subj["Périodo"] % 2 + 4
        self.Nodes[subj.name] = {
            "id": subj.name,
            "x": 600 * subj["Período"],
            "y": self.CANVAS_Y[subj["Período"]],
            "color": color,
            "nome": subj.name.split("-")[1],
        }
        self.CANVAS_Y[subj["Período"]] += 500

    def _setEdge(self, subj):
        if len(subj["Pré-Requisitos"]) > 1:
            for preReq in subj["Pré-Requisitos"]:
                self.Edges[f'{subj.name.split("-")[0]}- {preReq.split("-")[0]}'] = {
                    "fromNode": subj.name,
                    "fromSide": "left",
                    "toNode": subj["Pré-Requisitos"],
                    "toSide": "right",
                    "color": 0 if subj["Média"] != None else 1,
                }

    @staticmethod
    def _saveNode(
        id: str, x: int, y: int, color=0, nome: str = "", folder=f"Obsidian\\Subjects\\"
    ):
        if len(nome) < 25:
            height = 220
        elif len(nome) < 50:
            height = 260
        else:
            height = 300
        return f'{{"id":"{id}","type":"file","file":"{folder}{id}.md","width":440,"height":{height},"color":"{color}","x":{x},"y":{y}}}'

    @staticmethod
    def _saveEdge(
        id: str,
        fromNode: str,
        fromSide: Literal["top", "bottom", "left", "right"],
        toNode: str,
        toSide: Literal["top", "bottom", "left", "right"],
        color=0,
    ):
        return f'{{"id":"{id}","fromNode":"{fromNode}","fromSide":"{fromSide}","toNode":"{toNode}","toSide":"{toSide}","toEnd":"none","color":"{color}"}}'

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
                        folder=f"Subjects/",
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
        with open(f"{self.folder}PR03.canvas", "w", encoding="utf-8") as f:
            f.write(subjectCanva)


if __name__ == "__main__":
    siga = SIGAA()

    obsidian = Obsidian(
        gradeDF=siga.curriculo.df,
        historicoDF=siga.historico,
    )

    ...
