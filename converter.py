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
        
        with open(input_path, mode='r', encoding='utf-8-sig') as infile:
            raw_lines = infile.readlines()
            if not raw_lines:
                raise Exception("The selected file is completely empty.")
                
            data_rows = []
            for line in raw_lines:
                if line.strip():
                    data_rows.append([cell.strip() for cell in line.split('\t')])
            
            grouped_products = {}
            
            for row in data_rows[1:]:
                if len(row) < 13: 
                    continue
                    
                raw_desc = row[2] if len(row) > 2 else "Standard Wheel"
                raw_brand = row[3] if len(row) > 3 else "Generic"
                
                title = clean_title(raw_desc)
                handle = generate_handle(title)
                
                if handle not in grouped_products:
                    grouped_products[handle] = {
                        "Title": title,
                        "Vendor": raw_brand,
                        "Variants": []
                    }
                grouped_products[handle]["Variants"].append(row)

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
                
                for handle, product in grouped_products.items():
                    is_first_row = True
                    
                    for variant_row in product["Variants"]:
                        new_row = {h: "" for h in shopify_headers}
                        new_row["Handle"] = handle
                        
                        if is_first_row:
                            new_row["Title"] = product["Title"]
                            new_row["Vendor"] = product["Vendor"]
                            new_row["Type"] = "Rims"
                            new_row["Image Src"] = variant_row[18] if len(variant_row) > 18 else ""
                            
                            offset = variant_row[5] if len(variant_row) > 5 else ""
                            hub = variant_row[12] if len(variant_row) > 12 else ""
                            finish = variant_row[11] if len(variant_row) > 11 else ""
                            seat = variant_row[13] if len(variant_row) > 13 else ""
                            mat = variant_row[14] if len(variant_row) > 14 else ""
                            load = variant_row[15] if len(variant_row) > 15 else ""
                            cap = variant_row[16] if len(variant_row) > 16 else ""
                            cap_type = variant_row[17] if len(variant_row) > 17 else ""
                            struc_warr = variant_row[20] if len(variant_row) > 20 else ""
                            fin_warr = variant_row[21] if len(variant_row) > 21 else ""
                            
                            html_spec = "<h3>Product Specifications:</h3><ul>"
                            if offset: html_spec += f"<li><strong>Offset:</strong> {offset}</li>"
                            if hub: html_spec += f"<li><strong>Hub Bore:</strong> {hub}</li>"
                            if finish: html_spec += f"<li><strong>Finish:</strong> {finish}</li>"
                            if seat: html_spec += f"<li><strong>Seat Type:</strong> {seat}</li>"
                            if mat: html_spec += f"<li><strong>Material:</strong> {mat}</li>"
                            if load: html_spec += f"<li><strong>Max Load (Lbs):</strong> {load}</li>"
                            if cap: html_spec += f"<li><strong>Center Cap Part #:</strong> {cap}</li>"
                            if cap_type: html_spec += f"<li><strong>Center Cap Type:</strong> {cap_type}</li>"
                            if struc_warr: html_spec += f"<li><strong>Structure Warranty:</strong> {struc_warr}</li>"
                            if fin_warr: html_spec += f"<li><strong>Finish Warranty (Years):</strong> {fin_warr}</li>"
                            html_spec += "</ul>"
                            new_row["Body (HTML)"] = html_spec
                            
                            disco_status = variant_row[0].upper() if len(variant_row) > 0 else "NO"
                            if "YES" in disco_status or "Y" == disco_status:
                                new_row["Published"] = "False"
                                new_row["Status"] = "draft"
                            else:
                                new_row["Published"] = "True"
                                new_row["Status"] = "active"
                                
                            is_first_row = False
                        
                        new_row["Option1 Name"] = "Diameter"
                        new_row["Option1 Value"] = variant_row[9] if len(variant_row) > 9 else "Universal"
                        
                        new_row["Option2 Name"] = "Width"
                        new_row["Option2 Value"] = variant_row[10] if len(variant_row) > 10 else "Standard"
                        
                        p1 = variant_row[6] if len(variant_row) > 6 else ""
                        p2 = variant_row[7] if len(variant_row) > 7 else ""
                        p3 = variant_row[8] if len(variant_row) > 8 else ""
                        patterns = [p for p in [p1, p2, p3] if p and p.lower() != "blank" and p.lower() != ""]
                        new_row["Option3 Name"] = "Bolt Pattern"
                        new_row["Option3 Value"] = " | ".join(patterns) if patterns else "Universal"
                        
                        new_row["Variant SKU"] = variant_row[1] if len(variant_row) > 1 else ""
                        new_row["Variant Inventory Qty"] = default_stock
                        
                        new_row["Variant Inventory Tracker"] = "shopify"
                        new_row["Variant Inventory Policy"] = "deny"
                        new_row["Variant Fulfillment Service"] = "manual"
                        new_row["Variant Requires Shipping"] = "True"
                        new_row["Variant Taxable"] = "True"
                        new_row["Variant Price"] = "0.00"
                        
                        writer.writerow(new_row)
                        
        messagebox.showinfo("Success!", "Grid Conversion Complete!\n\nYour layout matches Shopify perfectly.")
    except Exception as e:
        messagebox.showerror("Error", f"Error during data mapping:\n\n{str(e)}")

def run_app():
    root = tk.Tk()
    root.title("Shopify Wheel Converter")
    root.geometry("450x200")
    root.resizable(False, False)
    
    def select_file():
        file_path = filedialog.askopenfilename(filetypes=[("Text/CSV Files", "*.csv *.txt")])
        if file_path: process_csv(file_path)

    tk.Label(root, text="Shopify Supplier CSV Formatter", font=("Arial", 14, "bold"), pady=20).pack()
    tk.Label(root, text="Select your supplier rim inventory file below to convert it.", font=("Arial", 10)).pack(pady=5)
    tk.Button(root, text="Select Supplier CSV File", command=select_file, bg="#4CAF50", fg="black", font=("Arial", 11, "bold"), padx=10, pady=10).pack(pady=15)
    
    root.mainloop()

if __name__ == "__main__":
    run_app()
