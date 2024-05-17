import argparse
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_page(page_number):
    url = "https://helios-cannabis.de/wp-admin/admin-ajax.php"
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "referer": "https://helios-cannabis.de/sortiment/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {
        "action": "filter_products",
        "nonce": "e383327630",
        "filter_data": "stock_status=on&stock_status_onbackorder=on&list_view=on",
        "posts_per_page": 12,
        "paged": page_number,
        "categories": "blueten,extrakte,shake",
        "attributes[]": [
            "pa_genetik",
            "pa_terpene",
            "pa_kultivar",
            "pa_thc-filter",
            "pa_cbd-filter",
            "pa_herkunftsland",
            "pa_hersteller",
            "kategorie",
            "list_view",
            "preis",
            "stock_status",
            "stock_status_onbackorder"
        ],
        "tableOrder[field]": "name",
        "tableOrder[order]": "ASC"
    }

    response = requests.post(url, data=data, headers=headers)
    return response.text

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    products = []

    for row in soup.select('tbody tr'):
        price_text = row.select_one('td:nth-child(6) div').text.strip()
        price = float(price_text.replace('€', '').replace(',', '.').strip())

        product = {
            'Lager': row.select_one('td:nth-child(1) div').get('class', [])[0].replace('product-status-round-', ''),
            'Name': row.select_one('td:nth-child(2)').text.strip(),
            'Kultivar': row.select_one('td:nth-child(3)').text.strip(),
            'THC/CBD': row.select_one('td:nth-child(4)').text.strip(),
            'Genetik': row.select_one('td:nth-child(5)').text.strip(),
            'Preis': price,
            'Link': row.select_one('td:nth-child(7) a').get('href')
        }
        products.append(product)

    return products

def fetch_all_pages():
    all_products = []
    page_number = 1

    while True:
        html = fetch_page(page_number)
        products = parse_html(html)
        
        if not products:
            break
        
        all_products.extend(products)
        page_number += 1
    
    return all_products

def export_to_html(catalogue, file_path):
    html_content = f"""
    <html>
    <head>
        <title>Helios Preisliste</title>
        <style>
            body {{background-color: #000; color: #fff;}}
            table {{width: 100%; border-collapse: collapse;}}
            th, td {{padding: 8px; text-align: left; border-bottom: 1px solid #ddd;}}
            th {{background-color: #444; cursor: pointer;}}
            .instock {{background-color: #2a5;}} /* green */
            .outofstock {{background-color: #fc3;}} /* yellow */
            .instock td, .outofstock td {{color: #000;}}
        </style>
        <script>
            function sortTable(n, numeric) {{
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("productTable");
                switching = true;
                dir = "asc";
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (numeric) {{
                            xContent = parseFloat(x.innerHTML);
                            yContent = parseFloat(y.innerHTML);
                        }} else {{
                            xContent = x.innerHTML.toLowerCase();
                            yContent = y.innerHTML.toLowerCase();
                        }}
                        if (dir == "asc") {{
                            if (xContent > yContent) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }} else if (dir == "desc") {{
                            if (xContent < yContent) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }}
                    }}
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    }} else {{
                        if (switchcount == 0 && dir == "asc") {{
                            dir = "desc";
                            switching = true;
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <table id="productTable">
            <tr>
                <th onclick="sortTable(0, false)">Lager</th>
                <th onclick="sortTable(1, true)">Preis</th>
                <th onclick="sortTable(2, false)">Name</th>
                <th onclick="sortTable(3, false)">Kultivar</th>
                <th onclick="sortTable(4, false)">THC/CBD</th>
                <th onclick="sortTable(5, false)">Genetik</th>
                <th>Link</th>
            </tr>
    """

    for product in catalogue:
        row_class = "instock" if product['Lager'] == "instock" else "outofstock"
        html_content += f"""
        <tr class="{row_class}">
            <td>{product['Lager']}</td>
            <td>{product['Preis']}</td>
            <td>{product['Name']}</td>
            <td>{product['Kultivar']}</td>
            <td>{product['THC/CBD']}</td>
            <td>{product['Genetik']}</td>
            <td><a href="{product['Link']}">Zum Produkt</a></td>
        </tr>
        """

    html_content += """
        </table>
        <script>
            if (Date.parse(document.lastModified) != 0) 
                document.write('<p><hr><small><i>Last modified: ' + document.lastModified + '</i></small>');
        </script>
    </body>
    </html>
    """

    with open(file_path, 'w') as file:
        file.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape and export product catalogue.')
    parser.add_argument('--export', type=str, help='Export catalogue to HTML file')

    args = parser.parse_args()

    catalogue = fetch_all_pages()
    catalogue.sort(key=lambda x: x['Preis'])

    if args.export:
        export_to_html(catalogue, args.export)
    else:
        print(json.dumps(catalogue, indent=2))

