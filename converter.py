import csv
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def clean_title(description, brand):
    """
    Cleans up the long supplier description to create a beautiful storefront title.
    Example: 'AIP MOT OFF-ROAD AGGRESSOR 17X10...' -> 'AIP MOT OFF-ROAD AGGRESSOR'
    """
    if not description:
        return "Standard Wheel Model"
    
    title = str(description).strip()
    
    # Look for common size patterns (like 17X10, 20X9, 18X10) and cut the text there
    size_match = re.search(r'\b\d{2}[xX]\d{1,2}\b', title)
    if size_match:
        title = title[:size_match.start()].strip()
        
    return title

def generate_handle(title):
    """Generates a clean URL link slug for Shopify"""
    handle = str(title).lower()
    handle = re.sub(r'[^a-z0-9\s-]', '', handle) # Remove special characters
    handle = re.sub(r'[\s-]+', '-', handle)      # Replace spaces with single dashes
    return handle.strip('-')

def find_column(headers, possibilities):
    """Helper to find a column name even if uppercase/lowercase varies"""
    for p in possibilities:
        for h in headers:
            if p.lower() in h.lower().strip():
                return h
    return None

def process_csv(input_path):
    try:
        # Automatically saves the output directly to the desktop user path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        output_path = os.path.join(desktop, "shopify_import_ready.csv")
        
        with open(input_path, mode='r', encoding='utf-8-sig') as infile:
            sample = infile.read(2048)
            dialect = csv.Sniffer().sniff(sample) if ',' in sample or ';' in sample else csv.excel
            infile.seek(0)
            
            reader = csv.DictReader(infile, dialect=dialect)
            headers = reader.fieldnames
            
            # --- Dynamically Find Column Headers ---
            brand_col = find_column(headers, ["brand", "mfg"])
            desc_col = find_column(headers, ["description", "desc"])
            sku_col = find_column(headers, ["sku", "item"])
            diam_col = find_column(headers, ["diameter", "size", "wheel dia"])
            width_col = find_column(headers, ["width", "wheel width"])
            bolt_col = find_column(headers, ["boltpattern", "bolt pattern", "pcd"])
            img_col = find_column(headers, ["image", "img", "pic"])
            disco_col = find_column(headers, ["discontinued", "disco"])
            
            # Search for stock column
            stock_col = find_column(headers, ["stock", "qty", "inventory", "avail", "on hand"])
            
            # Prompt user for a fallback inventory quantity if the supplier sheet doesn't track it
            default_stock = "0"
            if not stock_col:
                default_stock = simpledialog.askstring(
                    "Inventory Setup", 
                    "No Stock/Quantity column found in this file.\n\nWhat default stock quantity should we set for these rims? (e.g., 4 or 8):",
                    initialvalue="4"
                )
                if default_stock is None:  # User clicked cancel
                    return
            
            # Gather remaining technical spec columns for the description box
            exclude_cols = [brand_col, desc_col, sku_col, diam_col, width_col, bolt_col, img_col, disco_col]
            if stock_col:
                exclude_cols.append(stock_col)
            tech_fields = [h for h in headers if h not in exclude_cols]

            # Shopify target structure layout configuration
            shopify_headers = [
                "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
                "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value", "Option3 Name", "Option3 Value",
                "Variant SKU", "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
                "Variant Fulfillment Service", "Variant Price", "Variant Requires Shipping", "Variant Taxable", 
                "Image Src", "Status"
            ]
            
            with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=shopify_headers)
                writer.writeheader()
                
                for row in reader:
                    new_row = {h: "" for h in shopify_headers}
                    
                    # 1. Product Title & Brand Identity
                    raw_desc = row.get(desc_col, "")
                    raw_brand = row.get(brand_col, "Generic")
                    
                    cleaned_title = clean_title(raw_desc, raw_brand)
                    new_row["Title"] = cleaned_title
                    new_row["Handle"] = generate_handle(cleaned_title)
                    new_row["Vendor"] = raw_brand
                    new_row["Type"] = "Rims"
                    
                    # 2. Build the Technical Specification List (HTML)
                    html_spec = "<h3>Product Specifications:</h3><ul>"
                    for field in tech_fields:
                        val = row.get(field, "").strip()
                        if val:
                            html_spec += f"<li><strong>{field.title()}:</strong> {val}</li>"
                    html_spec += "</ul>"
                    new_row["Body (HTML)"] = html_spec
                    
                    # 3. Map Customer Dropdown Options (Variants)
                    new_row["Option1 Name"] = "Diameter"
                    new_row["Option1 Value"] = row.get(diam_col, "Universal")
                    
                    new_row["Option2 Name"] = "Width"
                    new_row["Option2 Value"] = row.get(width_col, "Standard")
                    
                    new_row["Option3 Name"] = "Bolt Pattern"
                    new_row["Option3 Value"] = row.get(bolt_col, "Universal")
                    
                    # 4. Inventory, SKUs, and Images
                    new_row["Variant SKU"] = row.get(sku_col, "")
                    new_row["Variant Inventory Qty"] = row.get(stock_col, default_stock)
                    new_row["Image Src"] = row.get(img_col, "")
                    
                    # 5. Automated Discontinued Safety Routing
                    is_discontinued = str(row.get(disco_col, "NO")).strip().upper()
                    if "YES" in is_discontinued or "Y" == is_discontinued:
                        new_row["Published"] = "False"
                        new_row["Status"] = "draft"  # Hide it safely inside Shopify admin
                    else:
                        new_row["Published"] = "True"
                        new_row["Status"] = "active" # Make it live for purchase
                    
                    # 6. Populate Shopify Required System Defaults
                    new_row["Variant Inventory Tracker"] = "shopify"
                    new_row["Variant Inventory Policy"] = "deny"
                    new_row["Variant Fulfillment Service"] = "manual"
                    new_row["Variant Requires Shipping"] = "True"
                    new_row["Variant Taxable"] = "True"
                    new_row["Variant Price"] = "0.00" 
                    
                    writer.writerow(new_row)
                    
        messagebox.showinfo("Success!", f"Format Conversion Complete!\n\nYour Shopify file has been saved to your Desktop as:\n'shopify_import_ready.csv'")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong processing the file:\n\n{str(e)}")

# --- Visual Interface Setup (GUI Window) ---
def run_app():
    root = tk.Tk()
    root.title("Shopify Wheel Converter")
    root.geometry("450x200")
    root.resizable(False, False)
    
    def select_file():
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            process_csv(file_path)

    label = tk.Label(root, text="Shopify Supplier CSV Formatter", font=("Arial", 14, "bold"), pady=20)
    label.pack()
    
    desc_label = tk.Label(root, text="Select your supplier rim inventory file below to convert it.", font=("Arial", 10))
    desc_label.pack(pady=5)
    
    btn = tk.Button(root, text="Select Supplier CSV File", command=select_file, bg="#4CAF50", fg="black", font=("Arial", 11, "bold"), padx=10, pady=10)
    btn.pack(pady=15)
    
    root.mainloop()

if __name__ == "__main__":
    run_app()
