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

def process_csv(input_path):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        output_path = os.path.join(desktop, "shopify_import_ready.csv")
        
        with open(input_path, mode='r', encoding='latin-1') as infile:
            raw_lines = infile.readlines()
            
        if not raw_lines:
            raise Exception("The selected file is completely empty.")
            
        data_rows = []
        for line in raw_lines:
            cleaned_line = line.strip()
            if cleaned_line:
                # --- FIXED: SPLIT ON MULTIPLE SPACES OR TABS AUTOMATICALLY ---
                # This breaks the row into a column box wherever 2 or more spaces exist
                split_row = re.split(r'\t|\s{2,}', cleaned_line)
                data_rows.append([cell.strip().strip('"') for cell in split_row])
        
        if len(data_rows) <= 1:
            raise Exception("No data rows found below the header line.")
            
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
        if default_stock is None: return
        
        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=shopify_headers, delimiter=',')
            writer.writeheader()
            
            row_count = 0
            
            for row in data_rows[1:]:
                # Check for bare minimum structural column parts
                if len(row) < 3:
                    continue
                
                row_count += 1
                new_row = {h: "" for h in shopify_headers}
                
                # --- DYNAMIC LAYER POSITION MAP ---
                discontinued_val = row[0].upper() if len(row) > 0 else "NO"
                sku_val = row[1] if len(row) > 1 else ""
                raw_desc = row[2] if len(row) > 2 else "Standard Wheel"
                brand_val = row[3] if len(row) > 3 else "Generic"
                offset_val = row[5] if len(row) > 5 else ""
                diam_val = row[9] if len(row) > 9 else "Universal"
                width_val = row[10] if len(row) > 10 else "Standard"
                finish_val = row[11] if len(row) > 11 else ""
                
                hub_val = row[12] if len(row) > 12 else ""
                seat_val = row[13] if len(row) > 13 else ""
                mat_val = row[14] if len(row) > 14 else ""
                load_val = row[15] if len(row) > 15 else ""
                cap_num = row[16] if len(row) > 16 else ""
                cap_type = row[17] if len(row) > 17 else ""
                img_val = row[18] if len(row) > 18 else ""
                struct_warr = row[20] if len(row) > 20 else ""
                finish_warr = row[21] if len(row) > 21 else ""
                
                cleaned_title = clean_title(raw_desc)
                new_row["Title"] = cleaned_title
                new_row["Handle"] = generate_handle(cleaned_title)
                new_row["Vendor"] = brand_val if brand_val else "Generic"
                new_row["Type"] = "Rims"
                new_row["Image Src"] = img_val
                
                # Build Description Specification Block dynamically
                html_spec = "<h3>Product Specifications:</h3><ul>"
                if offset_val: html_spec += f"<li><strong>Offset:</strong> {offset_val}</li>"
                if hub_val: html_spec += f"<li><strong>Hub Bore Metric:</strong> {hub_val}</li>"
                if finish_val: html_spec += f"<li><strong>Finish:</strong> {finish_val}</li>"
                if seat_val: html_spec += f"<li><strong>Seat Type:</strong> {seat_val}</li>"
                if mat_val: html_spec += f"<li><strong>Material:</strong> {mat_val}</li>"
                if load_val: html_spec += f"<li><strong>Max Load (Lbs):</strong> {load_val}</li>"
                if cap_num: html_spec += f"<li><strong>Center Cap Part #:</strong> {cap_num}</li>"
                if cap_type: html_spec += f"<li><strong>Center Cap Type:</strong> {cap_type}</li>"
                if struct_warr: html_spec += f"<li><strong>Structure Warranty:</strong> {struct_warr}</li>"
                if finish_warr: html_spec += f"<li><strong>Finish Warranty (Years):</strong> {finish_warr}</li>"
                html_spec += "</ul>"
                new_row["Body (HTML)"] = html_spec
                
                if "YES" in discontinued_val or "Y" == discontinued_val:
                    new_row["Published"] = "False"
                    new_row["Status"] = "draft"
                else:
                    new_row["Published"] = "True"
                    new_row["Status"] = "active"
                
                new_row["Option1 Name"] = "Diameter"
                new_row["Option1 Value"] = diam_val
                
                new_row["Option2 Name"] = "Width"
                new_row["Option2 Value"] = width_val
                
                p1 = row[6] if len(row) > 6 else ""
                p2 = row[7] if len(row) > 7 else ""
                p3 = row[8] if len(row) > 8 else ""
                patterns = [p for p in [p1, p2, p3] if p and p.lower() != "blank" and p.lower() != ""]
                new_row["Option3 Name"] = "Bolt Pattern"
                new_row["Option3 Value"] = " | ".join(patterns) if patterns else "Universal"
                
                new_row["Variant SKU"] = sku_val
                new_row["Variant Inventory Qty"] = default_stock
                new_row["Variant Inventory Tracker"] = "shopify"
                new_row["Variant Inventory Policy"] = "deny"
                new_row["Variant Fulfillment Service"] = "manual"
                new_row["Variant Requires Shipping"] = "True"
                new_row["Variant Taxable"] = "True"
                new_row["Variant Price"] = "0.00"
                
                writer.writerow(new_row)
                
            messagebox.showinfo("Success!", f"Conversion Complete!\n\nProcessed {row_count} rows successfully.\nSaved to Desktop.")
    except Exception as e:
        messagebox.showerror("Error", f"Error during position mapping:\n\n{str(e)}")

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
