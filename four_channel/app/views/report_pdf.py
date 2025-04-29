from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import textwrap
from pathlib import Path

def get_save_directory():
    usb_base_path = '/media'
    downloads_path = str(Path.home() / 'Downloads')

    # Check if any user folder exists inside /media
    if os.path.exists(usb_base_path):
        for user_folder in os.listdir(usb_base_path):
            user_path = os.path.join(usb_base_path, user_folder)
            if os.path.isdir(user_path):
                # Now check if any device inside user folder
                for device_folder in os.listdir(user_path):
                    device_path = os.path.join(user_path, device_folder)
                    if os.path.ismount(device_path):
                        return device_path, 'USB'

    # No USB found
    return downloads_path, 'Downloads'


@csrf_exempt
def report_pdf(request):
    if request.method == 'POST':
        from_date = request.POST.get('from_date', '')
        to_date = request.POST.get('to_date', '')
        mode = request.POST.get('mode', '')
        part_model = request.POST.get('part_model', '')
        shift = request.POST.get('shift', '')
        status = request.POST.get('status', '')
        total_count = request.POST.get('total_count', '')
        table_html = request.POST.get('table_html')

        if table_html:
            soup = BeautifulSoup(table_html, 'html.parser')
            rows = soup.find_all('tr')

            if not rows:
                return JsonResponse({'success': False, 'message': 'No table rows found.'})

            first_row = rows[0].find_all(['th', 'td'])
            col_count = len(first_row)

            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            file_name = f'report_data_{current_datetime}.pdf'

            save_dir, save_location = get_save_directory()

            # Make sure the folder exists
            os.makedirs(save_dir, exist_ok=True)

            file_path = os.path.join(save_dir, file_name)

            c = canvas.Canvas(file_path, pagesize=landscape(letter))
            width, height = landscape(letter)

            c.setFont("Helvetica-Bold", 8)

            # First Row (4 values)
            c.drawString(30, height - 40, f'From Date: {from_date}')
            c.drawString(200, height - 40, f'To Date: {to_date}')
            c.drawString(400, height - 40, f'Mode: {mode}')
            c.drawString(600, height - 40, f'Part Model: {part_model}')

            # Second Row (3 values)
            c.drawString(30, height - 60, f'Shift: {shift}')
            c.drawString(200, height - 60, f'Status: {status}')
            c.drawString(400, height - 60, f'Total Count: {total_count}')

            sr_no_width = 40  
            remaining_width = width - 60 - sr_no_width
            other_col_count = col_count - 1  
            col_width = remaining_width / other_col_count if other_col_count > 0 else remaining_width

            x_offset = 30
            y_offset = height - 75

            # Process headers
            c.setFont("Helvetica-Bold", 4)
            header_cells = rows[0].find_all(['th', 'td'])
            wrapped_headers = [textwrap.wrap(th.text.strip(), width=10) for th in header_cells]
            max_header_height = max(len(w) for w in wrapped_headers) * 5

            row_height = max_header_height + 12

            for i, wrapped_text in enumerate(wrapped_headers):
                col_w = sr_no_width if i == 0 else col_width
                x_text_offset = x_offset + (col_w / 2)

                total_text_height = len(wrapped_text) * 5
                y_text_offset = y_offset - ((row_height - total_text_height) / 2) - 5

                for line in wrapped_text:
                    text_width = c.stringWidth(line, "Helvetica-Bold", 4)
                    c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
                    y_text_offset -= 5

                c.rect(x_offset, y_offset - row_height, col_w, row_height)
                x_offset += col_w

            y_offset -= row_height

            # Process table rows
            row_limit = 30
            row_count = 0
            c.setFont("Helvetica", 4)

            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                x_offset = 30

                wrapped_texts = [textwrap.wrap(cell.text.strip(), width=10) for cell in cells]
                max_line_count = max(len(w) for w in wrapped_texts)

                row_height = max_line_count * 5 + 12

                for i, wrapped_text in enumerate(wrapped_texts):
                    col_w = sr_no_width if i == 0 else col_width
                    x_text_offset = x_offset + (col_w / 2)

                    total_text_height = len(wrapped_text) * 5
                    y_text_offset = y_offset - ((row_height - total_text_height) / 2) - 5

                    for line in wrapped_text:
                        text_width = c.stringWidth(line, "Helvetica", 4)
                        c.drawString(x_text_offset - (text_width / 2), y_text_offset, line)
                        y_text_offset -= 5

                    c.rect(x_offset, y_offset - row_height, col_w, row_height)
                    x_offset += col_w

                row_count += 1
                y_offset -= row_height

                if row_count >= row_limit:
                    c.showPage()
                    row_count = 0
                    y_offset = height - 50
                    c.setFont("Helvetica", 4)

            c.save()
            return JsonResponse({'success': True, 'message': f'PDF file has been saved successfully in your {save_location}: {file_path}'})

        else:
            return JsonResponse({'success': False, 'message': 'No table data provided.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
