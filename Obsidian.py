import pandas as pd
from typing import Literal
import os
import paths
from SIGAA import SIGAA


class Obsidian:
    def __init__(self, folder):
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def perfilToMD(self, subjectsDF):
        self.subjects = [ObsidianMD(subjectsDF.loc[subj]) for subj in subjectsDF.T]

    def saveMD(self):
        for subject in self.subjects:
            with open(f"{self.folder}\\{subject.nome}.md", "w", encoding="utf-8") as f:
                f.write(subject.MD)


class ObsidianMD(Obsidian):
    def __init__(self, subject):
        self.nome = subject.name
        self.periodo = subject["Período"]
        self.tipo = "".join(subject["Tipo"]).replace("'", "")
        self.chTotal = subject["CH Total"]
        self.preReq = self._FormatSubjectData(subject["Pré-Requisitos"])
        self.coReq = self._FormatSubjectData(subject["Co-Requisitos"])
        self.equiv = self._FormatSubjectData(subject["Equivalências"])
        self.ementa = "".join(subject["Ementa"]).replace("'", "")
        self.subject = self.SubjectToMD()

    def SubjectToMD(self):
        self.MD = f"""|**Período**|**Tipo**|**CH Total**|
|-|-|-|
| {self.periodo} | {self.tipo} | {self.chTotal} |
##### Pré-Requisitos
{self.preReq}
##### Có-Requisitos
{self.coReq}
##### Equivalências
{self.equiv}
##### Ementa
{self.ementa}
"""

    def _FormatSubjectData(self, subjectData):
        if isinstance(subjectData, list):
            if not subjectData:
                return ""
            else:
                return str("[[" + "]], [[".join(subjectData) + "]]").replace("'", "")
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
        else f"Obsidian\\"
    )
    obsidian.perfilToMD(PerfilCurricular)
    obsidian.saveMD()
    ...
