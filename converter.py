import csv
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def clean_title(description):
    if not description:
        return "Standard Wheel Model"
    title = str(description).strip()
    
    # Intelligently capture the Brand, Model, and Hub Bore before the size dimensions
    # Example: 'ARMED OFF-ROAD AGGRESSOR 87.1 20x10...' -> 'ARMED OFF-ROAD AGGRESSOR 87.1'
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
            # Parse using tab delimiters explicitly for your TSV file setup
            reader = csv.DictReader(infile, delimiter='\t')
            
            grouped_products = {}
            
            for row in reader:
                row = {str(k).strip(): str(v).strip() for k, v in row.items()}
                
                raw_desc = row.get("Description", "")
                raw_brand = row.get("Brand", "Generic")
                
                # Title and Handle will now unique-group by Hub Bore perfectly
                title = clean_title(raw_desc)
                handle = generate_handle(title)
                
                if handle not in grouped_products:
                    grouped_products[handle] = {
                        "Title": title,
                        "Vendor": raw_brand,
                        "Variants": []
                    }
                grouped_products[handle]["Variants"].append(row)

            # --- Target Shopify Column Mapping Configuration ---
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
                        
                        # --- 1. CORE DATA FIELDS (Now separating models properly) ---
                        if is_first_row:
                            new_row["Title"] = product["Title"]
                            new_row["Vendor"] = product["Vendor"]
                            new_row["Type"] = "Rims"
                            new_row["Image Src"] = variant_row.get("Image1", "")
                            
                            # Construct Technical Specification Box using exact headers
                            html_spec = "<h3>Product Specifications:</h3><ul>"
                            tech_keys = [
                                "OFFSET", "HUBBOREMETRIC", "SEATTYPE", "MATERIAL", 
                                "MaxLoadLbs", "CenterCapPartNumber", "CenterCapType", 
                                "StructureWarranty", "FinishWarranty(Years)"
                            ]
                            for key in tech_keys:
                                val = variant_row.get(key, "")
                                if val:
                                    html_spec += f"<li><strong>{key}:</strong> {val}</li>"
                            html_spec += "</ul>"
                            new_row["Body (HTML)"] = html_spec
                            
                            # Discontinued Status Layout Check
                            is_discontinued = variant_row.get("Discontinued", "NO").upper()
                            if "YES" in is_discontinued or "Y" == is_discontinued:
                                new_row["Published"] = "False"
                                new_row["Status"] = "draft"
                            else:
                                new_row["Published"] = "True"
                                new_row["Status"] = "active"
                                
                            is_first_row = False
                        
                        # --- 2. MULTI-OPTION CUSTOMER DROPDOWNS ---
                        new_row["Option1 Name"] = "Diameter"
                        new_row["Option1 Value"] = variant_row.get("WHEELDIAMETER", "Universal")
                        
                        new_row["Option2 Name"] = "Width"
                        new_row["Option2 Value"] = variant_row.get("WHEELWIDTH", "Standard")
                        
                        # Process multi-drill pattern layouts
                        p1 = variant_row.get("BOLTPATTERN1METRIC", "")
                        p2 = variant_row.get("BOLTPATTERN2METRIC", "")
                        p3 = variant_row.get("BOLTPATTERN3METRIC", "")
                        patterns = [p for p in [p1, p2, p3] if p and p.lower() != "blank"]
                        combined_patterns = " | ".join(patterns) if patterns else "Universal"
                        
                        new_row["Option3 Name"] = "Bolt Pattern"
                        new_row["Option3 Value"] = combined_patterns
                        
                        # --- 3. IDENTIFIERS ---
                        new_row["Variant SKU"] = variant_row.get("Item", "")
                        new_row["Variant Inventory Qty"] = default_stock
                        
                        # --- 4. SHOPIFY INVENTORY POLICY DEFAULTS ---
                        new_row["Variant Inventory Tracker"] = "shopify"
                        new_row["Variant Inventory Policy"] = "deny"
                        new_row["Variant Fulfillment Service"] = "manual"
                        new_row["Variant Requires Shipping"] = "True"
                        new_row["Variant Taxable"] = "True"
                        new_row["Variant Price"] = "0.00"
                        
                        writer.writerow(new_row)
                        
        messagebox.showinfo("Success!", "Flawless Data Separation Complete!\n\nYour formatted file is saved to your desktop.")
    except Exception as e:
        messagebox.showerror("Error", f"Error during structural build:\n\n{str(e)}")

def run_app():
    root = tk.Tk()
    root.title("Shopify Wheel Converter")
    root.geometry("450x200")
    root.resizable(False, False)
    
    def select_file():
        file_path = filedialog.askopenfilename(filetypes=[("Text/CSV Files", "*.csv;*.txt")])
        if file_path: process_csv(file_path)

    tk.Label(root, text="Shopify Supplier CSV Formatter", font=("Arial", 14, "bold"), pady=20).pack()
    tk.Label(root, text="Select your supplier rim inventory file below to convert it.", font=("Arial", 10)).pack(pady=5)
    tk.Button(root, text="Select Supplier CSV File", command=select_file, bg="#4CAF50", fg="black", font=("Arial", 11, "bold"), padx=10, pady=10).pack(pady=15)
    
    root.mainloop()

if __name__ == "__main__":
    run_app()
