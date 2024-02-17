import os
import pandas as pd
from pypdf import PdfReader


class calendar:
    def __init__(self, folder=f"data\\PlanoEnsino\\"):
        self.subjects = []
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if os.path.splitext(file)[1] == ".pdf":
                        self.subjects.append(
                            subjectPlan(subjPlanPdfPath=os.path.join(root, file))
                        )

    def to_csv(self):
        csvCalendar = pd.DataFrame()
        for subj in self.subjects:
            for classes in subj.classes:
                csvCalendar = pd.concat([csvCalendar, classes.df], ignore_index=True)

        csvCalendar.to_csv("teste.csv", index=False, encoding="utf-8-sig")


class subjectPlan:
    def __init__(self, subjPlanPdfPath):
        self.classes = []

        if os.path.isfile(subjPlanPdfPath):
            subjPlanPDF = PdfReader(subjPlanPdfPath)
            for page in subjPlanPDF.pages:
                text = page.extract_text(extraction_mode="layout")
                txtLines = [line for line in text.split("\n") if line != ""]
                for i, line in enumerate(txtLines):
                    if "PERÍODO" in line:
                        periodo = [i.strip() for i in line.split("   ") if i != ""][-1]

                    # Disciplina
                    elif "CH Teórica" in line:
                        name = [
                            clr.strip()
                            for clr in txtLines[i + 1].split("   ")
                            if clr != ""
                        ][0]
                    # Turma
                    elif "Turma" in line and "Identificação" in txtLines[i + 1]:
                        turma = [
                            clr.strip()
                            for clr in txtLines[i + 2].split("   ")
                            if clr != ""
                        ][0]

                    # Ementa
                    # Objetivo
                    # Metodologia
                    # Forma de Avaliação
                    # Bibliografia

                    # Unidade Programática
                    elif (
                        "Unidade Programática" in line and "Conteúdo" in txtLines[i + 1]
                    ):
                        skipNext = False
                        for j, lineUnit in enumerate(txtLines[i + 3 :]):
                            if skipNext:
                                skipNext = False
                                continue
                            fieldPos = [
                                (0, 13),
                                (14, 65),
                                (66, 77),
                                (78, 87),
                                (87, 97),
                                (98, 109),
                                (110, 120),
                                (120, None),
                            ]
                            if "Status do Relatório" in lineUnit:
                                break
                            elif "Data de Envio" in lineUnit:
                                break
                            elif "Data de Aprovação" in lineUnit:
                                break
                            elif "/" in lineUnit and ":" in lineUnit:
                                data = []
                                for k, piece in enumerate(
                                    [
                                        i.strip()
                                        for i in lineUnit.split("    ")
                                        if i != ""
                                    ]
                                ):
                                    firstPiece = piece.strip()
                                    nextPiece = txtLines[i + j + 4][
                                        fieldPos[k][0] : fieldPos[k][1]
                                    ].strip()
                                    end = firstPiece + " " + nextPiece
                                    skipNext = True
                                    data.append(end.strip())
                            self.classes.append(
                                calendarItem(
                                    name=name,
                                    description=f"""Turma {turma}
Professor:{data[-1]}
Conteúdo:{data[1]}""",
                                    startDate=data[0].split(" ")[0],
                                    startTime=data[2],
                                    endTime=data[3],
                                )
                            )
                        break


class calendarItem:
    def __init__(
        self,
        name,
        startDate,
        endDate=None,
        startTime=None,
        endTime=None,
        allDay=True,
        description=None,
        location=None,
        Private=False,
    ):
        self.att = {
            "Subject": name,
            "Start Date": startDate,
        }
        if endDate:
            self.att["End Date"] = endDate
        else:
            self.att["End Date"] = startDate
        if startTime:
            self.att["All Day Event"] = "FALSE"
            self.att["Start Time"] = self.setHour(startTime)
            self.att["End Time"] = self.setHour(endTime)
        else:
            self.att["All Day Event"] = "TRUE"

        if description:
            self.att["Description"] = description
        if location:
            self.att["Location"] = location

        self.df = pd.DataFrame(self.att, index=[0])

    # MISSING
    def setHour(self, str):
        return str


if __name__ == "__main__":
    newCal = calendar()

    calendarTest = calendarItem(
        name="Teste",
        startDate="02/17/2024",
        description=f"""Teste de descrição. \n\nIsso ae ?""",
        location=f"Sala 12 Teste",
        startTime="10:00:00",
        endTime="12:00:00",
    )
    newCal.to_csv()

    print("Main Done")
