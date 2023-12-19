import pandas as pd
from typing import Literal
import paths


ObsidianFolder = paths.ObsidianFolder


####################
# Obsidian CANVAS
####################
def SetNode(id: str, x: int, y: int, color=0, nome: str = ""):
    if len(nome) < 25:
        height = 220
    elif len(nome) < 50:
        height = 260
    else:
        height = 300
    return f'{{"id":"{id}","type":"file","file":"PlanoMaterias/Subjects/{id}.md","width":440,"height":{height},"color":"{color}","x":{x},"y":{y}}}'


def SetEdge(
    id: str,
    fromNode: str,
    fromSide: Literal["top", "bottom", "left", "right"],
    toNode: str,
    toSide: Literal["top", "bottom", "left", "right"],
    color=0,
):
    return f'{{"id":"{id}","fromNode":"{fromNode}","fromSide":"{fromSide}","toNode":"{toNode}","toSide":"{toSide}","toEnd":"none","color":"{color}"}}'


CANVAS_Y = [0] * 11
Nodes = pd.DataFrame(index=["color", "x", "y", "nome"])
Edges = pd.DataFrame(index=["fromNode", "fromSide", "toNode", "toSide", "color"])


def SubjectToCANVAS(subjectDF):
    global CANVAS_Y
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
    Nodes[CODIGO] = [
        color,
        600 * PERIODO,
        CANVAS_Y[PERIODO],
        NOME,
    ]
    CANVAS_Y[PERIODO] += 500

    for preReq in preRequisitos:
        Edges[f"{CODIGO}-{preReq}"] = [
            CODIGO,
            "left",
            preReq,
            "right",
            0 if preReq in aprovadas else 1,
        ]


####################
# PerfilCurricular to MD
####################
def FormatSubjectData(subjectData):
    if isinstance(subjectData, list):
        if not subjectData:
            return ""
        else:
            return str("[[" + "]], [[".join(subjectData) + "]]").replace("'", "")
    return subjectData


def SubjectToMD(subjectDF):
    global SumPeriodos
    CODIGO, NOME, *_ = subjectDF.name.split(" - ")
    periodo = subjectDF["Período"]
    conteudo = f"""### {NOME}
|**Período**|**Tipo**|**CH Total**|
|-|-|-|
| {periodo} | {''.join(subjectDF['Tipo']).replace("'", "")} | {subjectDF['CH Total']} |
##### Pré-Requisitos
{FormatSubjectData(subjectDF['Pré-Requisitos'])}
##### Có-Requisitos
{FormatSubjectData(subjectDF['Co-Requisitos'])}
##### Equivalências
{FormatSubjectData(subjectDF['Equivalências'])}
##### Ementa
{''.join(subjectDF['Ementa']).replace("'", "")}
"""
    with open(f"{ObsidianFolder}Subjects\\{CODIGO}.md", "w", encoding="utf-8") as f:
        f.write(conteudo)


####################
# Main
####################
# Histórico
historico = pd.read_excel("Historico.xlsx", index_col=0)
aprovadas = [
    i.split(" - ")[0]
    for i in historico.loc[
        historico["Situação"].isin(["APROVADO POR MÉDIA", "DISPENSADO"])
    ].index
]
print("Histórico Processado")

# Perfil
PerfilCurricular = pd.read_excel("PRO03.xlsx", index_col=0).T
PerfilCurricular = PerfilCurricular.applymap(
    lambda x: [i for i in x.strip("[]").replace("", "").split(", ") if i != ""]
    if isinstance(x, str)
    else x
)
print("Grade Processada")

# Subject to MD
for subject in PerfilCurricular:
    SubjectToMD(PerfilCurricular[subject])
    SubjectToCANVAS(PerfilCurricular[subject])
print("Cards Gerados")

# Set Color by Needed
sumPreRequisitos = pd.Series([Edges[edge]["toNode"] for edge in Edges]).value_counts()
for subject in sumPreRequisitos.keys():
    selectedSubjects = [
        Edges[edge].name for edge in Edges if Edges[edge]["toNode"] == subject
    ]
    for edge in selectedSubjects:
        if Edges[edge]["color"] != 0:
            if sumPreRequisitos[subject] > 2:
                Edges[edge]["color"] = 1
            elif sumPreRequisitos[subject] > 1:
                Edges[edge]["color"] = 2
            else:
                Edges[edge]["color"] = 4
print("Edges ajustadas")

# Order Y by sumPreRequisitos
sortedSubjects = sumPreRequisitos.sort_values(ascending=False)
periodos = Nodes.loc["x"].unique()

for periodo in periodos:
    subjects_in_period = Nodes.columns[Nodes.loc["x"] == periodo]
    subjects_series = pd.Series(
        {
            subject: sortedSubjects[subject] if subject in sortedSubjects else 0
            for subject in subjects_in_period
        }
    )
    subjects_in_period = subjects_series.sort_values(ascending=False).index

    for i, subject in enumerate(subjects_in_period):
        x_coord = Nodes.loc["x", subject]
        y_coord = 500 * i
        Nodes.loc["y", subject] = y_coord
print("Nodes reordenados")

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
            SetNode(
                id=Nodes[node].name,
                x=Nodes[node]["x"],
                y=Nodes[node]["y"],
                color=Nodes[node]["color"],
                nome=Nodes[node]["nome"],
            )
            for node in Nodes
        ]
    ),
    ",\n\t\t".join(
        [
            SetEdge(
                id=Edges[edge].name,
                fromNode=Edges[edge]["fromNode"],
                fromSide=Edges[edge]["fromSide"],
                toNode=Edges[edge]["toNode"],
                toSide=Edges[edge]["toSide"],
                color=Edges[edge]["color"],
            )
            for edge in Edges
        ]
    ),
)

with open(f"{ObsidianFolder}PR03.canvas", "w", encoding="utf-8") as f:
    f.write(subjectCanva)
