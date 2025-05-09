import os
from django.http import JsonResponse
from weasyprint import HTML
from datetime import datetime


from pathlib import Path

def get_save_directory():
    usb_base_path = '/media'
    downloads_path = str(Path.home() / 'Downloads')

    if os.path.exists(usb_base_path):
        for user_folder in os.listdir(usb_base_path):
            user_path = os.path.join(usb_base_path, user_folder)
            if os.path.isdir(user_path):
                for device_folder in os.listdir(user_path):
                    device_path = os.path.join(user_path, device_folder)
                    if os.path.ismount(device_path):
                        return device_path, 'USB'
    return downloads_path, 'Downloads'

def spc_download(request):
    if request.method == 'POST':
        table_html = request.POST.get('table_html', '')
        chart_html = request.POST.get('chart_html', '')

        from_date = request.POST.get('from_date', '')
        to_date = request.POST.get('to_date', '')
        part_model = request.POST.get('part_model', '')
        mode = request.POST.get('mode', '')
        shift = request.POST.get('shift', '')
        parameter_name = request.POST.get('parameter_name', '')
        sample_size = request.POST.get('sample_size', '')

        summary_table_html = f"""
        <table>
            <tr>
                <th>From Date</th>
                <td>{from_date}</td>
                <th>To Date</th>
                <td>{to_date}</td>
            </tr>
            <tr>
                <th>Part Model</th>
                <td>{part_model}</td>
                <th>Mode</th>
                <td>{mode}</td>
            </tr>
            <tr>
                <th>Shift</th>
                <td>{shift}</td>
                <th>Sample Size</th>
                <td>{sample_size}</td>
            </tr>
            <tr>
                <th>Parameter Name</th>
                <td colspan="3">{parameter_name}</td>
            </tr>
        </table>
        """

        full_html = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 10mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 9px;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }}
                h2 {{
                    text-align: center;
                    margin: 4px 0 8px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 8px;
                    table-layout: fixed;
                    word-wrap: break-word;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 2px;
                    text-align: center;
                }}
                img {{
                    max-width: 100%;
                    max-height: 300px;
                    height: auto;
                    display: block;
                    margin: 0 auto 10px auto;
                }}
                .section {{
                    page-break-inside: avoid;
                    max-height: 350px;
                    overflow: hidden;
                }}
            </style>
        </head>
        <body>
            <h2>SPC Report</h2>
            {summary_table_html}
            <div class="section">{chart_html}</div>
            <div class="section">{table_html}</div>
        </body>
        </html>
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{mode}_{timestamp}.pdf"
        save_dir, source = get_save_directory()
        save_path = os.path.join(save_dir, filename)

        try:
            HTML(string=full_html).write_pdf(save_path)
            return JsonResponse({'success': True, 'message': f'PDF saved to: {save_path} ({source})'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
