import csv
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def clean_title(description):
    if not description:
        return "Standard Wheel Model"
    title = str(description).strip()
    size_match = re.search(r'\b\d{2}[xX]\d{1,2}\b', title)
    if size_match:
        title = title[:size_match.start()].strip()
    return title

def generate_handle(title):
    handle = str(title).lower()
    handle = re.sub(r'[^a-z0-9\s-]', '', handle)
    handle = re.sub(r'[\s-]+', '-', handle)
    return handle.strip('-')

def get_reader_with_encoding(input_path):
    encodings_to_try = ['utf-8-sig', 'utf-16', 'latin-1']
    for enc in encodings_to_try:
        try:
            f = open(input_path, mode='r', encoding=enc)
            sample = f.read(1024)
            f.seek(0)
            if not sample or '\0' in sample: 
                f.close()
                continue
            reader = csv.DictReader(f, delimiter='\t')
            headers = reader.fieldnames
            if headers and any("Description" in h for h in headers):
                return f, reader
            f.close()
        except Exception:
            if 'f' in locals() and not f.closed:
                f.close()
            continue
    f = open(input_path, mode='r', encoding='utf-8', errors='ignore')
    reader = csv.DictReader(f, delimiter='\t')
    return f, reader

def process_csv(input_path):
    file_obj = None
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        output_path = os.path.join(desktop, "shopify_import_ready.csv")
        file_obj, reader = get_reader_with_encoding(input_path)
        shopify_headers = [
            "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
            "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", "Option3 Name", "Option3 Value",
            "Variant SKU", "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
            "Variant Fulfillment Service", "Variant Price", "Variant Requires Shipping", "Variant Taxable", 
            "Image Src", "Status"
        ]
        default_stock = simpledialog.askstring(
            "Inventory Setup", 
            "What default stock quantity should we set for these rims? (e.g., 4 or 8):",
            initialvalue="4"
        )
        if default_stock is None: 
            file_obj.close()
            return
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=shopify_headers, delimiter=',')
            writer.writeheader()
            row_count = 0
            for row in reader:
                row = {str(k).strip(): str(v).strip() for k, v in row.items() if k is not None}
                raw_desc = row.get("Description", "")
                if not raw_desc:
                    raw_desc = row.get("DESCRIPTION", "")
                if not raw_desc:
                    continue
                row_count += 1
                new_row = {h: "" for h in shopify_headers}
                cleaned_title = clean_title(raw_desc)
                new_row["Title"] = cleaned_title
                new_row["Handle"] = generate_handle(cleaned_title)
                new_row["Vendor"] = row.get("Brand", "Generic")
                new_row["Type"] = "Rims"
                new_row["Image Src"] = row.get("Image1", "")
                html_spec = "<h3>Product Specifications:</h3><ul>"
                tech_keys = [
                    "OFFSET", "HUBBOREMETRIC", "SEATTYPE", "MATERIAL", 
                    "MaxLoadLbs", "CenterCapPartNumber", "CenterCapType", 
                    "StructureWarranty", "FinishWarranty(Years)"
                ]
                for key in tech_keys:
                    val = row.get(key, "")
                    if val:
                        html_spec += f"<li><strong>{key}:</strong> {val}</li>"
                html_spec += "</ul>"
                new_row["Body (HTML)"] = html_spec
                is_discontinued = row.get("Discontinued", "NO").upper()
                if "YES" in is_discontinued or "Y" == is_discontinued:
                    new_row["Published"] = "False"
                    new_row["Status"] = "draft"
                else:
                    new_row["Published"] = "True"
                    new_row["Status"] = "active"
                new_row["Option1 Name"] = "Diameter"
                new_row["Option1 Value"] = row.get("WHEELDIAMETER", "Universal")
                new_row["Option2 Name"] = "Width"
                new_row["Option2 Value"] = row.get("WHEELWIDTH", "Standard")
                p1 = row.get("BOLTPATTERN1METRIC", "")
                p2 = row.get("BOLTPATTERN2METRIC", "")
                p3 = row.get("BOLTPATTERN3METRIC", "")
                patterns = [p for p in [p1, p2, p3] if p and p.lower() != "blank" and p.lower() != ""]
                new_row["Option3 Name"] = "Bolt Pattern"
                new_row["Option3 Value"] = " | ".join(patterns) if patterns else "Universal"
                new_row["Variant SKU"] = row.get("Item", "")
                new_row["Variant Inventory Qty"] = default_stock
                new_row["Variant Inventory Tracker"] = "shopify"
                new_row["Variant Inventory Policy"] = "deny"
                new_row["Variant Fulfillment Service"] = "manual"
                new_row["Variant Requires Shipping"] = "True"
                new_row["Variant Taxable"] = "True"
                new_row["Variant Price"] = "0.00"
                writer.writerow(new_row)
        file_obj.close()
        if row_count == 0:
            messagebox.showwarning("Warning", "File processed but 0 rows were written.\n\nDouble check that your file headers match exactly: 'Description', 'Brand', etc.")
        else:
            messagebox.showinfo("Success!", f"Conversion Complete!\n\nProcessed {row_count} rows.\nSaved to: {output_path}")
    except Exception as e:
        if file_obj: file_obj.close()
        messagebox.showerror("Error", f"Error during processing:\n\n{str(e)}")

def run_app():
    root = tk.Tk()
    root.title("Shopify Wheel Converter")
    root.geometry("450x200")
    root.resizable(False, False)
    def select_file():
        file_path = filedialog.askopenfilename()
        if file_path: process_csv(file_path)
    tk.Label(root, text="Shopify Supplier CSV Formatter", font=("Arial", 14, "bold"), pady=20).pack()
    tk.Label(root, text="Select your supplier rim inventory file below.", font=("Arial", 10)).pack(pady=5)
    tk.Button(root, text="Select Supplier File", command=select_file, bg="#4CAF50", fg="black", font=("Arial", 11, "bold"), padx=10, pady=10).pack(pady=15)
    root.mainloop()

if __name__ == "__main__":
    run_app()
