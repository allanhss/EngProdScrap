import os
import pandas as pd
from pypdf import PdfReader


class calendar:
    def __init__(self, folder=f"data\\PlanoEnsino\\"):
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        else:
            for root, dirs, files in os.walk(self.folder):
                for file in files:
                    if os.path.splitext(file)[1] == ".pdf":
                        subjectPlan(subjPlanPdfPath=os.path.join(root, file))

    def to_csv(): ...


class subjectPlan:
    def __init__(self, subjPlanPdfPath):
        if os.path.isfile(subjPlanPdfPath):
            subjPlanPDF = PdfReader(subjPlanPdfPath)
            for page in subjPlanPDF.pages:
                text = page.extract_text(extraction_mode="layout")


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
    calendarTest.df.to_csv("teste.csv", index=False, encoding="utf-8-sig")
    # newCal.to_csv()
    print("Main Done")
