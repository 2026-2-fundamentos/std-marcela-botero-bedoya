from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "ventas.csv"
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "ventas.csv"

SUPPLIER_REPLACEMENTS = {
    "amazon web services colombia": "Amazon Web Services Colombia",
    "BANCOLOMBIA S.A.": "Bancolombia S.A.",
    "Cementos Argos SA": "Cementos Argos S.A.",
    "cementos argos s.a.": "Cementos Argos S.A.",
    "Corona SAS": "Corona S.A.S.",
    "Ecopetrol  S.A.": "Ecopetrol S.A.",
    "GOOGLE COLOMBIA LTDA.": "Google Colombia Ltda.",
    "Grupo  Éxito  S.A.": "Grupo Éxito S.A.",
    "IBM Colombia SAS.": "IBM Colombia S.A.S.",
    "ibm colombia s.a.s.": "IBM Colombia S.A.S.",
    "MICROSOFT COLOMBIA INC.": "Microsoft Colombia Inc.",
    "Nutresa SA": "Nutresa S.A.",
    "nutresa s.a.": "Nutresa S.A.",
    "oracle colombia ltda.": "Oracle Colombia Ltda.",
    "POSTOBÓN S.A.": "Postobon S.A.",
    "SAP Colombia SAS": "SAP Colombia S.A.S.",
    "Schneider  Electric": "Schneider Electric",
    "SIEMENS S.A.S.": "Siemens S.A.S.",
    "siemens s.a.s.": "Siemens S.A.S.",
    "Sura  S.A.": "Sura S.A.",
    "Telefónica  Colombia": "Telefónica Colombia",
}


COUNTRY_REPLACEMENTS = {
    "CO": "COL",
    "COLOMBIA": "COL",
    "Colombia": "COL",
    "colombia": "COL",
}

CITY_REPLACEMENTS = {
    "bogotá": "Bogotá",
    "BOGOTÁ": "Bogotá",
    "Medellin": "Medellín",
    "medellín": "Medellín",
    "MEDELLÍN": "Medellín",
}


def clean_column_names(df):
    # Casos tipicos en la columna
    # ' Supplier ID ' -> "supplier_id"
    # 'City ' -> "city"
    # 'Purchase Date' -> "purchase_date"
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def clean_supplier_column(df):
    df["supplier"] = df["supplier"].str.strip()
    df["supplier"] = df["supplier"].replace(SUPPLIER_REPLACEMENTS)
    return df


def clean_country_column(df):
    df["country"] = df["country"].str.strip()
    df["country"] = df["country"].replace(COUNTRY_REPLACEMENTS)
    return df


def clean_city_column(df):
    df["city"] = df["city"].str.strip()
    df["city"] = df["city"].replace(CITY_REPLACEMENTS)
    return df


def clean_purchase_date_column(df):

    def convert_yyyy_s_mm_s_dd_to_yyyy_mm_dd(series):
        # Convierte fechas en formato "YYYY/MM/DD" a "YYYY-MM-DD"
        series = series.str.replace(r"(\d{4})/(\d{2})/(\d{2})", r"\1-\2-\3", regex=True)
        return series

    def convert_mmddyyyy_to_yyyy_mm_dd(series):
        # Corrige solo fechas con el día primero, cuando el día es mayor que 12.
        def convert_date(match):
            g1, g2, g3 = match.groups()
            if int(g2) > 12:  # el dia aparece en la mitad
                return f"{g3}-{g1}-{g2}"
            return f"{g3}-{g2}-{g1}"

        return series.str.replace(r"(\d{2})/(\d{2})/(\d{4})", convert_date, regex=True)

    def convert_dd_mm_yyyy_to_yyyy_mm_dd_separated_with_dots(series):
        # Corrige fechas en formato "DD.MM.YYYY" a "YYYY-MM-DD"
        return series.str.replace(r"(\d{2})\.(\d{2})\.(\d{4})", r"\3-\2-\1", regex=True)

    def convert_dd_mm_yy_to_yyyy_mm_dd_separated_with_hyphens(series):
        # Corrige fechas en formato "DD-MM-YY" a "YYYY-MM-DD"
        return series.str.replace(
            r"^(\d{2})-(\d{2})-(\d{2})$", r"20\3-\2-\1", regex=True
        )

    df["purchase_date"] = df["purchase_date"].str.strip()
    df["purchase_date"] = convert_yyyy_s_mm_s_dd_to_yyyy_mm_dd(df["purchase_date"])
    df["purchase_date"] = convert_mmddyyyy_to_yyyy_mm_dd(df["purchase_date"])
    df["purchase_date"] = convert_dd_mm_yyyy_to_yyyy_mm_dd_separated_with_dots(
        df["purchase_date"]
    )
    df["purchase_date"] = convert_dd_mm_yy_to_yyyy_mm_dd_separated_with_hyphens(
        df["purchase_date"]
    )

    return df


def clean_amount_column(df):

    def clean_strings_ending_with_k(series):
        # Convierte valores como "1.5K" a "1500"
        def convert_value(value):
            if isinstance(value, str) and value.endswith("K"):
                try:
                    return int(float(value[:-1]) * 1000)
                except ValueError:
                    return value
            return value

        return series.apply(convert_value)

    def clean_strings_starting_with_COP(series):
        # Convierte valores como "COP 1,250,000" a "1250000"
        def convert_value(value):
            if isinstance(value, str) and value.startswith("COP"):
                try:
                    return int(value[3:].replace(",", "").strip())
                except ValueError:
                    return value
            return value

        return series.apply(convert_value)

    def clean_strings_starting_with_dollar(series):
        # Convierte valores como "$1,250,000" a "1250000"
        def convert_value(value):
            if isinstance(value, str) and value.startswith("$"):
                try:
                    return int(value[1:].replace(",", "").strip())
                except ValueError:
                    return value
            return value

        return series.apply(convert_value)

    def remove_dots(series):
        # Elimina los puntos de los valores numéricos
        def convert_value(value):
            if isinstance(value, str):
                try:
                    return int(value.replace(".", "").strip())
                except ValueError:
                    return value
            return value

        return series.apply(convert_value)

    df["amount"] = df["amount"].str.strip()
    df["amount"] = clean_strings_ending_with_k(df["amount"])
    df["amount"] = clean_strings_starting_with_COP(df["amount"])
    df["amount"] = clean_strings_starting_with_dollar(df["amount"])
    df["amount"] = remove_dots(df["amount"])

    return df


def clean_discount_column(df):
    # Limpia la columna de descuento
    df["discount"] = df["discount"].str.strip()
    df["discount"] = df["discount"].str.replace("%", "", regex=False)
    df["discount"] = df["discount"].astype(float)
    df["discount"] = df["discount"].map(lambda x: x / 100 if x > 1 else x)

    return df

def clean_weight_column(df):
    # Limpia la columna de peso y la deja en kg
    # "50000 g" -> 50.0 | "0.0050 ton" -> 5.0 | "5 kg" -> 5.0 | "12" -> 12.0
    def convert_value(value):
        if pd.isna(value):
            return value
        value = str(value).strip().lower().replace(",", ".")
        if value.endswith(" ton"):
            return float(value[:-4]) * 1000
        if value.endswith(" kg"):
            return float(value[:-3])
        if value.endswith(" g"):
            return float(value[:-2]) / 1000
        return float(value)

    df["weight"] = df["weight"].map(convert_value).astype(float)
    return df


def clean_units_column(df):
    # Limpia la columna de unidades
    # Se usa Int64 para conservar los vacíos sin convertirlos a decimales.
    def convert_value(value):
        if pd.isna(value):
            return pd.NA
        value = str(value).strip().lower().replace("units", "").replace("unit", "")
        return int(float(value))

    df["units"] = df["units"].map(convert_value).astype("Int64")
    return df


def clean_unit_price_column(df):
    # Limpia la columna de precio unitario
    # "$49,000.00" -> 49000.0 | "1.750.000.00" -> 1750000.0 | "48000.00" -> 48000.0
    def convert_value(value):
        if pd.isna(value):
            return value
        value = str(value).strip().replace("$", "").replace(",", "")
        # Si hay varios puntos, solo el último es el decimal; los demás son miles
        if value.count(".") > 1:
            integer_part, decimal_part = value.rsplit(".", 1)
            value = integer_part.replace(".", "") + "." + decimal_part
        return float(value)

    df["unit_price"] = df["unit_price"].map(convert_value).astype(float)
    return df


def clean_contact_email_column(df):
    # Limpia la columna de correo electrónico de contacto
    # "sin correo" (u otro valor sin formato de correo) -> vacío
    df["contact_email"] = df["contact_email"].str.strip().str.lower()
    valid = df["contact_email"].str.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", na=False)
    df.loc[~valid, "contact_email"] = pd.NA
    return df


def main():
    df = pd.read_csv(INPUT_FILE, dtype=str, encoding="utf-8-sig")
    df = clean_column_names(df)
    df = clean_supplier_column(df)
    df = clean_country_column(df)
    df = clean_city_column(df)
    df = clean_purchase_date_column(df)
    df = clean_amount_column(df)
    df = clean_discount_column(df)
    df = clean_weight_column(df)
    df = clean_units_column(df)
    df = clean_unit_price_column(df)
    df = clean_contact_email_column(df)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()