import os
import requests
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from datetime import datetime, timedelta
from reportlab.lib.units import mm

# Constants
API_URL = "https://api.verkada.com/cameras/v1/devices"
PAGE_LIMIT = 200
API_KEY = os.getenv("VERKADA_API_KEY")
if not API_KEY:
    raise ValueError("Command REST API key not found. Please set the VERKADA_API_KEY environment variable.")

def fetch_camera_data():
    headers = {
        "x-api-key": f"{API_KEY}",
        "accept": "application/json"
    }
    cameras = []
    page = 1
    while True:
        response = requests.get(API_URL, headers=headers, params={"page_token": page, "page_limit": PAGE_LIMIT})
        data = response.json()
        cameras.extend(data['cameras'])
        if len(data['cameras']) < PAGE_LIMIT:
            break
        page += 1
    return cameras

def group_cameras_by_site(cameras):
    sites = {}
    for camera in cameras:
        site = camera['site']
        if site not in sites:
            sites[site] = []
        sites[site].append(camera)
    return sites

def create_camera_status_by_site_bar_graph(sites):
    for site, cameras in sites.items():
        status_counts = {"Live": 0, "Offline": 0}
        for camera in cameras:
            status_counts[camera['status']] += 1
        labels = list(status_counts.keys())
        sizes = list(map(int, status_counts.values())) 
        
        plt.figure(figsize=(3, 2))  
        bars = plt.bar(labels, sizes, color=['green', 'red'], width=0.15)  
        plt.xlabel('Status', fontsize=14)
        plt.ylabel('Cameras', fontsize=14)
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        plt.tight_layout()
        plt.savefig(f"{site}_status_bar.png", dpi=150, bbox_inches='tight')

def create_camera_growth_bar_graph(cameras):
    date_counts = {}
    one_year_ago = datetime.now() - timedelta(days=365)
    one_year_ago_epoch = int(one_year_ago.timestamp())
    
    for camera in cameras:
        install_date_epoch = camera['date_added']
        if install_date_epoch > one_year_ago_epoch:
            install_date = datetime.fromtimestamp(install_date_epoch)
            month = install_date.strftime('%Y-%m')
            if month not in date_counts:
                date_counts[month] = 0
            date_counts[month] += 1
    
    dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in dates]
    
    plt.figure(figsize=(6, 4))
    plt.bar(dates, counts)
    plt.xlabel('Month')
    plt.ylabel('Number of Cameras Installed')
    plt.title('Camera Count Growth Over the Past Year')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("camera_growth_bar.png", dpi=150, bbox_inches='tight')

def create_pdf_report(sites):
    def add_header(canvas, doc):
        header_text = f"Report Date: {datetime.now().strftime('%Y-%m-%d')}"
        canvas.drawRightString(200 * mm, 280 * mm, header_text)

    doc = SimpleDocTemplate("Verkada_Camera_Report.pdf", pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    elements = []

    # Add logo image
    logo_path = "verkada_logo.png"
    elements.append(Spacer(1, 12))
    elements.append(Image(logo_path, width=100, height=50))
    elements.append(Spacer(1, 12))

    # Title with current date
    report_title = "Verkada Install Site Report"
    report_date = f"Report Created On: {datetime.now().strftime('%Y-%m-%d')}"
    elements.append(Table([[report_title]], style=[
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    elements.append(Spacer(1, 12))

    # Sort sites alphabetically
    sorted_sites = sorted(sites.items())

    for site, cameras in sorted_sites:
        # Title with site name
        site_title = f"Site: {site}"
        elements.append(Table([[site_title]], style=[
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ]))
        elements.append(Spacer(1, 12))

        # Add status bar graph image
        bar_image_path = f"{site}_status_bar.png"
        elements.append(Image(bar_image_path, width=250, height=125))
        elements.append(Spacer(1, 12))

        # Table data
        data = [["Name", "Model", "Serial", "Date Added"]]
        for camera in cameras:
            date_added = datetime.fromtimestamp(camera['date_added']).strftime('%Y-%m-%d')
            data.append([
                camera['name'],
                camera['model'],
                camera['serial'],
                date_added
            ])
            count += 1

        # Create table
        table = Table(data, colWidths=[150, 60, 120, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0293cd')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 24))

    doc.build(elements, onFirstPage=add_header, onLaterPages=add_header)

def main():
    cameras = fetch_camera_data()
    sites = group_cameras_by_site(cameras)
    create_camera_status_by_site_bar_graph(sites)
    create_camera_growth_bar_graph(cameras)
    create_pdf_report(sites)

if __name__ == "__main__":
    main()
