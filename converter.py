import csv
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def clean_title(description):
    if not description:
        return "Standard Wheel Model"
    title = str(description).strip()
    # Look for standard rim dimensions (like 20x10, 17x9) to slice clean storefront titles
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
            # Safely forces reading by tab dividers to handle your file layout flawlessly
            reader = csv.DictReader(infile, delimiter='\t')
            
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
                
                for row in reader:
                    # Strip any invisible formatting wrapper spacing around the text columns
                    row = {str(k).strip(): str(v).strip() for k, v in row.items()}
                    
                    # Skip empty padding lines
                    if not row.get("Description"):
                        continue
                        
                    new_row = {h: "" for h in shopify_headers}
                    
                    # 1. Product Identity and URL link configurations
                    raw_desc = row.get("Description", "")
                    cleaned_title = clean_title(raw_desc)
                    new_row["Title"] = cleaned_title
                    new_row["Handle"] = generate_handle(cleaned_title)
                    new_row["Vendor"] = row.get("Brand", "Generic")
                    new_row["Type"] = "Rims"
                    new_row["Image Src"] = row.get("Image1", "")
                    
                    # 2. Bundle all remaining technical info into the Description box list
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
                    
                    # 3. Handle Discontinued Safety Check
                    is_discontinued = row.get("Discontinued", "NO").upper()
                    if "YES" in is_discontinued or "Y" == is_discontinued:
                        new_row["Published"] = "False"
                        new_row["Status"] = "draft"
                    else:
                        new_row["Published"] = "True"
                        new_row["Status"] = "active"
                    
                    # 4. Map the Dropdown menu fields for sizes
                    new_row["Option1 Name"] = "Diameter"
                    new_row["Option1 Value"] = row.get("WHEELDIAMETER", "Universal")
                    
                    new_row["Option2 Name"] = "Width"
                    new_row["Option2 Value"] = row.get("WHEELWIDTH", "Standard")
                    
                    # Process and stitch multi-drill layout patterns cleanly
                    p1 = row.get("BOLTPATTERN1METRIC", "")
                    p2 = row.get("BOLTPATTERN2METRIC", "")
                    p3 = row.get("BOLTPATTERN3METRIC", "")
                    patterns = [p for p in [p1, p2, p3] if p and p.lower() != "blank" and p.lower() != ""]
                    new_row["Option3 Name"] = "Bolt Pattern"
                    new_row["Option3 Value"] = " | ".join(patterns) if patterns else "Universal"
                    
                    # 5. Inventory Tracking Codes and Defaults
                    new_row["Variant SKU"] = row.get("Item", "")
                    new_row["Variant Inventory Qty"] = default_stock
                    new_row["Variant Inventory Tracker"] = "shopify"
                    new_row["Variant Inventory Policy"] = "deny"
                    new_row["Variant Fulfillment Service"] = "manual"
                    new_row["Variant Requires Shipping"] = "True"
                    new_row["Variant Taxable"] = "True"
                    new_row["Variant Price"] = "0.00"
                    
                    writer.writerow(new_row)
                    
        messagebox.showinfo("Success!", "Flawless Conversion Complete!\n\nYour file has been saved directly to your Desktop.")
    except Exception as e:
        messagebox.showerror("Error", f"Error during structural build:\n\n{str(e)}")

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
