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

    def add_event(self, event):
        self.subjects.append(event)

    def to_csv(self, output_file="teste.csv"):
        csv_calendar = pd.DataFrame()
        for subj in self.subjects:
            for classes in subj.classes:
                csv_calendar = pd.concat([csv_calendar, classes.df], ignore_index=True)

        csv_calendar.to_csv(output_file, index=False, encoding="utf-8-sig")


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
            "End Date": end_date if end_date else start_date,
            "All Day Event": "TRUE" if all_day else "FALSE",
        }
        if start_time:
            self.att["Start Time"] = self.set_hour(start_time)
            self.att["End Time"] = self.set_hour(end_time)

        if description:
            self.att["Description"] = description
        if location:
            self.att["Location"] = location

        self.df = pd.DataFrame(self.att, index=[0])

    def set_hour(self, time_str):
        # Convertendo a hora para o formato HH:MM AM/PM
        try:
            time_obj = pd.to_datetime(time_str, format="%H:%M")
            return time_obj.strftime("%I:%M %p")
        except ValueError:
            return time_str


class SubjectPlan:
    def __init__(self, subjPlanPdfPath=None):
        self.classes = []
        if subjPlanPdfPath and os.path.isfile(subjPlanPdfPath):
            subj_plan_pdf = PdfReader(subjPlanPdfPath)
            for page in subj_plan_pdf.pages:
                text = page.extract_text()
                txt_lines = [line for line in text.split("\n") if line != ""]
                self.parse_lines(txt_lines)

    def parse_lines(self, lines):
        for i, line in enumerate(lines):
            if "Unidade Programática" in line:
                self.parse_programmatic_unit(lines[i + 1 :])
                break

    def parse_programmatic_unit(self, lines):
        for line in lines:
            try:
                # Verificar se a linha contém uma data no formato esperado (dd/mm/yyyy)
                if len(line) >= 10 and line[2] == "/" and line[5] == "/":
                    # Data encontrada
                    parts = line.split()
                    date = parts[0]
                    content_index = 1
                    while not parts[content_index].isdigit():
                        content_index += 1
                    content = " ".join(parts[1:content_index])
                    start_time = parts[content_index]
                    end_time = parts[content_index + 2]

                    start_date = pd.to_datetime(date, format="%d/%m/%Y").strftime(
                        "%Y/%m/%d"
                    )
                    self.classes.append(
                        CalendarItem(
                            name=content,
                            start_date=start_date,
                            start_time=start_time,
                            end_time=end_time,
                            all_day=False,
                            description="Aula de Cálculo III",
                            location="Sala de Aula",
                        )
                    )
            except (ValueError, IndexError):
                continue


if __name__ == "__main__":
    new_cal = Calendar("data\\PlanoEnsino")

    # Adicionando eventos ao calendário
    new_cal.add_event(SubjectPlan("data\\PlanoEnsino\\PlanoEnsino - Calculo 3.pdf"))

    # Exportar para CSV
    new_cal.to_csv("calendar_test.csv")

    print("Main Done")
