import os
import pandas as pd
from pypdf import PdfReader


class Calendar:
    def __init__(self, folder="data\\PlanoEnsino"):
        self.subjects = []
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if os.path.splitext(file)[1] == ".pdf":
                        self.subjects.append(
                            SubjectPlan(subjPlanPdfPath=os.path.join(root, file))
                        )

    def to_csv(self):
        csv_calendar = pd.DataFrame()
        for subj in self.subjects:
            for classes in subj.classes:
                csv_calendar = pd.concat([csv_calendar, classes.df], ignore_index=True)

        csv_calendar.to_csv("teste.csv", index=False, encoding="utf-8-sig")


class CalendarItem:
    def __init__(
        self,
        name,
        start_date,
        end_date=None,
        start_time=None,
        end_time=None,
        all_day=True,
        description=None,
        location=None,
        private=False,
    ):
        self.att = {
            "Subject": name,
            "Start Date": start_date,
        }
        if end_date:
            self.att["End Date"] = end_date
        else:
            self.att["End Date"] = start_date
        if start_time:
            self.att["All Day Event"] = "FALSE"
            self.att["Start Time"] = self.set_hour(start_time)
            self.att["End Time"] = self.set_hour(end_time)
        else:
            self.att["All Day Event"] = "TRUE"

        if description:
            self.att["Description"] = description
        if location:
            self.att["Location"] = location

        self.df = pd.DataFrame(self.att, index=[0])

    def set_hour(self, time_str):
        return time_str


class SubjectPlan:
    def __init__(self, subjPlanPdfPath):
        self.classes = []

        if os.path.isfile(subjPlanPdfPath):
            subj_plan_pdf = PdfReader(subjPlanPdfPath)
            for page in subj_plan_pdf.pages:
                text = page.extract_text()
                txt_lines = [line for line in text.split("\n") if line != ""]
                for i, line in enumerate(txt_lines):
                    if "PERÍODO" in line:
                        periodo = [i.strip() for i in line.split("   ") if i != ""][-1]

                    elif "CH Teórica" in line:
                        name = [
                            clr.strip()
                            for clr in txt_lines[i + 1].split("   ")
                            if clr != ""
                        ][0]

                    elif "Turma" in line and "Identificação" in txt_lines[i + 1]:
                        turma = [
                            clr.strip()
                            for clr in txt_lines[i + 2].split("   ")
                            if clr != ""
                        ][0]

                    elif (
                        "Unidade Programática" in line
                        and "Conteúdo" in txt_lines[i + 1]
                    ):
                        skip_next = False
                        for j, line_unit in enumerate(txt_lines[i + 3 :]):
                            if skip_next:
                                skip_next = False
                                continue
                            field_pos = [
                                (0, 13),
                                (14, 65),
                                (66, 77),
                                (78, 87),
                                (87, 97),
                                (98, 109),
                                (110, 120),
                                (120, None),
                            ]
                            if "Status do Relatório" in line_unit:
                                break
                            elif "Data de Envio" in line_unit:
                                break
                            elif "Data de Aprovação" in line_unit:
                                break
                            elif "/" in line_unit and ":" in line_unit:
                                data = []
                                for k, piece in enumerate(
                                    [
                                        i.strip()
                                        for i in line_unit.split("    ")
                                        if i != ""
                                    ]
                                ):
                                    first_piece = piece.strip()
                                    next_piece = txt_lines[i + j + 4][
                                        field_pos[k][0] : field_pos[k][1]
                                    ].strip()
                                    end = first_piece + " " + next_piece
                                    skip_next = True
                                    data.append(end.strip())
                                if len(data) >= 4:
                                    self.classes.append(
                                        CalendarItem(
                                            name=name,
                                            description=f"""Turma {turma}
Professor:{data[-1]}
Conteúdo:{data[1]}""",
                                            start_date=data[0].split(" ")[0],
                                            start_time=data[2],
                                            end_time=data[3],
                                        )
                                    )
                        break


if __name__ == "__main__":
    new_cal = Calendar()

    calendar_test = CalendarItem(
        name="Teste",
        start_date="02/17/2024",
        description="Teste de descrição. \n\nIsso ae ?",
        location="Sala 12 Teste",
        start_time="10:00:00",
        end_time="12:00:00",
    )
    new_cal.to_csv()

    print("Main Done")
