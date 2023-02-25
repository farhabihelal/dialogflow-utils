import pandas as pd


def read_xlsx(db_path) -> dict:
    db = {}
    xls = pd.ExcelFile(db_path)

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet)
        db[sheet] = df

    return db
