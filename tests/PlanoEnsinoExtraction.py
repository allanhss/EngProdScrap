import os
import pandas as pd
from pypdf import PdfReader


def extract_events_from_pdf(pdf_path):
    events = []
    if os.path.isfile(pdf_path):
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            text = page.extract_text()
            lines = [line for line in text.split("\n") if line.strip()]
            events.extend(parse_lines(lines))
    return events


def parse_lines(lines):
    events = []
    capture = False
    for line in lines:
        if "Unidade Programática" in line:
            capture = True
            continue
        if "PERÍODO LETIVO" in line:
            break
        if capture:
            parts = line.split()
            if len(parts) > 1 and parts[0].count("/") == 2:
                date = parts[0]
                content = " ".join(parts[1:])
                events.append((date, content))
    return events


def print_events(events):
    for date, content in events:
        print(f"Data: {date}, Conteúdo: {content}")


if __name__ == "__main__":
    pdf_path = "data\\PlanoEnsino\\PlanoEnsino - Calculo 3.pdf"
    events = extract_events_from_pdf(pdf_path)
    print_events(events)
