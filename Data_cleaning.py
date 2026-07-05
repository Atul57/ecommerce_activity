import re
import numpy as np
import pandas as pd

df = pd.read_csv("messy_ecommerce_sales_data.csv", dtype=str)
df.columns = [c.strip() for c in df.columns]  # " Category" -> "Category"

# print(df.shape)
# print(df.head())

text_cols = ["Customer_Name", "Product", "Payment_Method", "Status", "Order_ID"]
for col in text_cols:
    df[col] = df[col].str.strip()

def clean_category(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    if val == "" or val.lower() == "nan":
        return np.nan
    if val.lower() in ("electronic", "electronics"):
        return "Electronics"
    return val.title()

df["Category"] = df["Category"].apply(clean_category)
# print(df["Category"].value_counts(dropna=False))

df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
# print(df["Order_Date"].isna().sum(), "rows with unparseable dates")

def clean_quantity(val):
    if pd.isna(val):
        return np.nan
    digits = re.sub(r"[^\d\-]", "", str(val))  # keep only digits and minus sign
    if digits in ("", "-"):
        return np.nan
    return abs(int(digits))  # treat negatives as sign errors

df["Quantity"] = df["Quantity"].apply(clean_quantity)

WORD_NUMS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

def clean_price(val):
    if pd.isna(val):
        return np.nan
    cleaned = str(val).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        pass
    words = cleaned.lower().split()
    if len(words) == 2 and words[1] == "hundred" and words[0] in WORD_NUMS:
        return float(WORD_NUMS[words[0]] * 100)
    return np.nan  # unrecoverable, e.g. "abd"

df["Price"] = df["Price"].apply(clean_price)

df["Total"] = (df["Quantity"] * df["Price"]).round(2)

n_before = len(df)
df = df.drop_duplicates()
print(f"Removed {n_before - len(df)} exact duplicate rows")

n_before = len(df)
df = df.dropna(how="any")
print(f"Removed {n_before - len(df)} rows with at least one empty field")

n_before = len(df)
df = df.dropna(subset=["Price", "Quantity", "Category", "Order_Date"])
print(f"Removed {n_before - len(df)} rows missing critical fields")

key_dupes = df.duplicated(subset=["ID", "Order_ID"], keep=False)
missing_critical = df["Price"].isna() | df["Quantity"].isna() | df["Category"].isna() | df["Order_Date"].isna()

review_df = df[key_dupes | missing_critical]
print(f"{len(review_df)} rows flagged for review")

df["ID"] = df["ID"].astype(int)
df["Order_Date"] = df["Order_Date"].dt.strftime("%Y-%m-%d")

df = df.sort_values("ID").reset_index(drop=True)

df.to_csv("cleaned_ecommerce_sales_data.csv", index=False)
review_df.to_csv("rows_needing_review.csv", index=False)