import csv
import os
import re
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, messagebox


INPUT_ENCODING = "latin-1"
OUTPUT_FILENAME = "shopify_import_ready.csv"


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_title(description, model=None):
    text = normalize_text(description)
    if not text:
        text = normalize_text(model) or "Wheel"

    # Trim common size fragments from descriptions when present.
    # Example: "Aggressor 20x10 Black" -> "Aggressor"
    size_match = re.search(r"\b\d{2}\s*[xX]\s*\d{1,2}\b", text)
    if size_match:
        text = text[: size_match.start()].strip()

    return text or "Wheel"


def slugify(value):
    value = normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value)
    return value.strip("-") or "wheel"


def yes_no(value):
    value = normalize_text(value).upper()
    return value in {"YES", "Y", "TRUE", "1", "DISCONTINUED"}


def make_bolt_pattern(row):
    patterns = []
    for key in ["BOLTPATTERN1METRIC", "BOLTPATTERN2METRIC", "BOLTPATTERN3METRIC"]:
        val = normalize_text(row.get(key, ""))
        if val and val.lower() != "blank":
            patterns.append(val)
    return " | ".join(patterns) if patterns else "Universal"


def make_size(row):
    dia = normalize_text(row.get("WHEELDIAMETER", ""))
    width = normalize_text(row.get("WHEELWIDTH", ""))
    if dia and width:
        return f"{dia}x{width}"
    return dia or width or ""


def make_variant_sku(row):
    sku = normalize_text(row.get("Item", ""))
    if sku:
        return sku
    brand = normalize_text(row.get("Brand", ""))
    model = normalize_text(row.get("Model", ""))
    finish = normalize_text(row.get("FINISH", ""))
    size = make_size(row)
    bolt = make_bolt_pattern(row)
    offset = normalize_text(row.get("OFFSET", ""))
    raw = " | ".join([p for p in [brand, model, finish, size, bolt, offset] if p])
    return slugify(raw).upper()


def build_body_html(group_rows):
    first = group_rows[0]
    brand = normalize_text(first.get("Brand", ""))
    model = normalize_text(first.get("Model", ""))
    finish = normalize_text(first.get("FINISH", ""))
    hub_bore = normalize_text(first.get("HUBBOREMETRIC", ""))
    seat_type = normalize_text(first.get("SEATTYPE", ""))
    material = normalize_text(first.get("MATERIAL", ""))
    load_rating = normalize_text(first.get("MaxLoadLbs", ""))
    center_cap = normalize_text(first.get("CenterCapPartNumber", ""))
    center_cap_type = normalize_text(first.get("CenterCapType", ""))
    structure_warranty = normalize_text(first.get("StructureWarranty", ""))
    finish_warranty = normalize_text(first.get("FinishWarranty(Years)", ""))

    sizes = sorted({make_size(r) for r in group_rows if make_size(r)})
    bolt_patterns = sorted({make_bolt_pattern(r) for r in group_rows if make_bolt_pattern(r)})
    offsets = sorted({normalize_text(r.get("OFFSET", "")) for r in group_rows if normalize_text(r.get("OFFSET", ""))})

    html = [
        "<p><strong>Contact us for pricing.</strong></p>",
        "<h3>Product Specifications</h3>",
        "<ul>",
    ]

    if brand:
        html.append(f"<li><strong>Brand:</strong> {brand}</li>")
    if model:
        html.append(f"<li><strong>Model:</strong> {model}</li>")
    if finish:
        html.append(f"<li><strong>Finish:</strong> {finish}</li>")
    if sizes:
        html.append(f"<li><strong>Available Sizes:</strong> {', '.join(sizes)}</li>")
    if bolt_patterns:
        html.append(f"<li><strong>Bolt Pattern(s):</strong> {', '.join(bolt_patterns)}</li>")
    if offsets:
        html.append(f"<li><strong>Offset(s):</strong> {', '.join(offsets)}</li>")
    if hub_bore:
        html.append(f"<li><strong>Hub Bore Metric:</strong> {hub_bore}</li>")
    if seat_type:
        html.append(f"<li><strong>Seat Type:</strong> {seat_type}</li>")
    if material:
        html.append(f"<li><strong>Material:</strong> {material}</li>")
    if load_rating:
        html.append(f"<li><strong>Max Load (Lbs):</strong> {load_rating}</li>")
    if center_cap:
        html.append(f"<li><strong>Center Cap Part #:</strong> {center_cap}</li>")
    if center_cap_type:
        html.append(f"<li><strong>Center Cap Type:</strong> {center_cap_type}</li>")
    if structure_warranty:
        html.append(f"<li><strong>Structure Warranty:</strong> {structure_warranty}</li>")
    if finish_warranty:
        html.append(f"<li><strong>Finish Warranty (Years):</strong> {finish_warranty}</li>")

    html.append("</ul>")
    return "\n".join(html)


def build_product_title(brand, model, finish):
    pieces = [normalize_text(brand), normalize_text(model)]
    base = " ".join([p for p in pieces if p]).strip() or "Wheel"
    if normalize_text(finish):
        return f"{base} - {finish}"
    return base


def process_csv(input_path):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop, exist_ok=True)
    output_path = os.path.join(desktop, OUTPUT_FILENAME)

    with open(input_path, "r", encoding=INPUT_ENCODING, newline="") as infile:
        reader = csv.DictReader(infile)
        rows = [row for row in reader]

    if not rows:
        raise ValueError("No data rows found in the supplier file.")

    # Group by brand/model/finish and discontinued state so draft items never mix with active ones.
    grouped = defaultdict(list)
    for row in rows:
        brand = normalize_text(row.get("Brand", ""))
        model = normalize_text(row.get("Model", ""))
        finish = normalize_text(row.get("FINISH", ""))
        discontinued = yes_no(row.get("Discontinued", ""))

        group_key = (brand, model, finish, discontinued)
        grouped[group_key].append(row)

    shopify_headers = [
        "Handle",
        "Title",
        "Body (HTML)",
        "Vendor",
        "Type",
        "Tags",
        "Published",
        "Option1 Name",
        "Option1 Value",
        "Option2 Name",
        "Option2 Value",
        "Option3 Name",
        "Option3 Value",
        "Variant SKU",
        "Variant Inventory Tracker",
        "Variant Inventory Qty",
        "Variant Inventory Policy",
        "Variant Fulfillment Service",
        "Variant Price",
        "Variant Requires Shipping",
        "Variant Taxable",
        "Image Src",
        "Image Position",
        "Image Alt Text",
        "Variant Image",
        "Status",
    ]

    product_count = 0
    variant_count = 0

    with open(output_path, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=shopify_headers)
        writer.writeheader()

        for (brand, model, finish, discontinued), group_rows in sorted(grouped.items()):
            product_count += 1

            title = build_product_title(brand, model, finish)
            handle = slugify(title)

            status = "draft" if discontinued else "active"
            published = "FALSE" if discontinued else "TRUE"

            body_html = build_body_html(group_rows)
            vendor = brand or "Generic"
            product_type = "Wheels"
            tags = ", ".join([t for t in [brand, model, finish, "wheels"] if t])

            # Keep variants compact and under 100 per product:
            # Option 1 = Size, Option 2 = Bolt Pattern, Option 3 = Offset
            seen_variants = set()
            seen_images = set()

            sorted_rows = sorted(
                group_rows,
                key=lambda r: (
                    normalize_text(r.get("WHEELDIAMETER", "")),
                    normalize_text(r.get("WHEELWIDTH", "")),
                    normalize_text(r.get("OFFSET", "")),
                    make_bolt_pattern(r),
                    normalize_text(r.get("Item", "")),
                ),
            )

            for idx, row in enumerate(sorted_rows, start=1):
                size = make_size(row)
                bolt = make_bolt_pattern(row)
                offset = normalize_text(row.get("OFFSET", ""))

                variant_key = (size, bolt, offset)
                if variant_key in seen_variants:
                    # If the supplier file repeats the same fitment row, skip duplicates.
                    continue
                seen_variants.add(variant_key)

                image_url = normalize_text(row.get("Image1", "")) or normalize_text(row.get("Image2", ""))
                sku = make_variant_sku(row)

                out = {h: "" for h in shopify_headers}
                out["Handle"] = handle
                out["Title"] = title if idx == 1 else ""
                out["Body (HTML)"] = body_html if idx == 1 else ""
                out["Vendor"] = vendor if idx == 1 else ""
                out["Type"] = product_type if idx == 1 else ""
                out["Tags"] = tags if idx == 1 else ""
                out["Published"] = published if idx == 1 else ""
                out["Status"] = status if idx == 1 else ""

                out["Option1 Name"] = "Size"
                out["Option1 Value"] = size
                out["Option2 Name"] = "Bolt Pattern"
                out["Option2 Value"] = bolt
                out["Option3 Name"] = "Offset"
                out["Option3 Value"] = offset

                out["Variant SKU"] = sku
                out["Variant Inventory Tracker"] = ""
                out["Variant Inventory Qty"] = "0"
                out["Variant Inventory Policy"] = "deny"
                out["Variant Fulfillment Service"] = "manual"
                out["Variant Price"] = "0.00"
                out["Variant Requires Shipping"] = "TRUE"
                out["Variant Taxable"] = "TRUE"
                out["Variant Image"] = image_url

                # Use the first image on the first row for the product image, and only once per image URL.
                if image_url and image_url not in seen_images:
                    out["Image Src"] = image_url
                    out["Image Position"] = str(len(seen_images) + 1)
                    alt = f"{title} - {size} - {bolt}"
                    out["Image Alt Text"] = alt[:512]
                    seen_images.add(image_url)

                writer.writerow(out)
                variant_count += 1

    return output_path, product_count, variant_count


def select_file():
    file_path = filedialog.askopenfilename(
        title="Select Supplier CSV",
        filetypes=[("CSV Files", "*.csv")]
    )
    if not file_path:
        return

    try:
        output_path, product_count, variant_count = process_csv(file_path)
        messagebox.showinfo(
            "Success",
            f"Created {product_count} products and {variant_count} variants.\n\nSaved to:\n{output_path}"
        )
    except Exception as e:
        messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    root.title("Shopify Wheel Converter")
    root.geometry("460x220")
    root.resizable(False, False)

    tk.Label(
        root,
        text="ATW → Shopify Converter",
        font=("Arial", 14, "bold")
    ).pack(pady=18)

    tk.Label(
        root,
        text="Select the supplier CSV and export a Shopify import file.",
        font=("Arial", 10)
    ).pack(pady=4)

    tk.Button(
        root,
        text="Select Supplier CSV",
        command=select_file,
        padx=18,
        pady=10
    ).pack(pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
