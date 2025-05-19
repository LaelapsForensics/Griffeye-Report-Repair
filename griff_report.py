"""
Griffeye Report Repair
author: Kevin Salhoff

Reads in Griffeye CSV report and properly links them to exported media based on hash value.
Utilizes ffmpeg to generate thumbnail that will be included in HTML report

Report should have all videos in 'media' subdirectory.  Thumbnails will be generated and placed
into 'thumbnails' subdirectory

Run from command line: 'python griff_report.py path_to_report'.  Prompts will request analyst
name, case number and item number for inclusion in final HTML report.
"""
from pathlib import Path
import os
import subprocess
import shutil
import argparse
import hashlib
import sys
import sqlite3
from datetime import timedelta


md5 = {}
sha1 = {}
conn = sqlite3.connect(":memory:")
c = conn.cursor()
column_headers = []
html_page = []
working_title = ""

try:
    parser = argparse.ArgumentParser()
    parser.add_argument("entered_path", help="Enter path to report folder and csv")
    args = parser.parse_args()
    working_path = args.entered_path
    print(working_path)
    name = input("Enter your name: ")
    case_num = input("Enter the Case Number: ")
    item_num = input("Enter the Item Number: ")


except:
    e = sys.exc_info()[0]
    print(e)


def create_tables(csv_file):
    with open(csv_file, "r") as f:
        col_headers = f.readline().rstrip()
        all_lines = []
        for line in f:
            lines = [line.rstrip()]
            all_lines.append(lines)

    table_setup = "CREATE TABLE 'griffeye' ('id'    INTEGER,"
    cols = col_headers.split(",")
    for x in cols:
        x = ''.join(e for e in x if e.isalnum())
        table_setup += " '" + x + "'    TEXT,"

    table_setup += " PRIMARY KEY('id' AUTOINCREMENT))"
    c.execute(table_setup)
    insert_into(all_lines, cols)

    return col_headers


def insert_into(row_list, columns):
    insert_query = "INSERT INTO 'griffeye' ("
    for x in columns:
        x = ''.join(e for e in x if e.isalnum())
        insert_query += x + ", "

    insert_query = insert_query[:-2] + ") VALUES ("
    pristine_query = insert_query

    for x in row_list:
        for y in x:
            row = y.split(",")
            for a in row:
                insert_query += "\"" + a + "\", "
            insert_query = insert_query[:-2] + ")"
            c.execute(insert_query)

            insert_query = pristine_query               # Reset Query

    conn.commit()


def initialize_table(html, name, casenum, itemnum, title, columns):
    html.append("""<!DOCTYPE html>
                    <html lang="en">
                    <head>
                    <meta charset="UTF-8">""")

    html.append("<title>" + title + "</title>")

    html.append("""<style>
                      body {
                        font-family: Arial, sans-serif;
                        text-align: center; /* Center align everything in the body */
                      }
                      .logo {
                        margin-top: 20px; /* Adds space above the logo */
                      }
                      .title {
                        margin: 20px 0; /* Adds space above and below the title */
                      }
                      .title2 {
                        margin: 20px 0; /* Adds space above and below the title2 */
                      }
                      .author {
                        margin-bottom: 20px; /* Adds space below the author's name */
                      }
                      .table-container {
                        margin: 0 auto; /* This centers the table container */
                        width: 100%; /* This sets the width of the table container to 100% */
                      }
                      table {
                        width: 100%; /* The table will now take 100% of the .table-container width */
                        border-collapse: collapse;
                        margin-top: 20px;
                      }
                      th, td {
                        border: 4px solid gray;
                        padding: 8px;
                        text-align: left; /* Align table cell content to left */
                      }
                      th {
                        background-color: #D6EAF8;
                      }
                      img {
                        width: 150px; /* Adjust the width to make thumbnails larger */
                        height: auto; /* Height is set to auto to maintain the aspect ratio */
                      }
                      /* Center table within body */
                      .table-container {
                        margin: 0 auto;
                        text-align: left;
                      }
                    </style>
                    </head>
                    <body>

                    <div class="logo">
                      <img src="media\logo.png" alt="Logo" style="width: 200px; height: auto;"/> 
                    </div>

                    <div class="title">""")

    html.append("<h2>" + title + "</h2>")

    html.append("""</div>
                    <div class="title2">""")

    html.append("<h2>" + casenum + "    Item " + itemnum + "</h2>")

    html.append("""</div>
                    <div class="author">""")

    html.append("<p>" + name + "</p>")

    html.append("""</div>

                    <div class="table-container">
                      <table>
                        <tr><th>#</th><th>Video</th>""")

    headers = columns.split(",")
    for i in headers:
        html.append("<th>" + i + "</th>")

    html.append("</tr>")


def get_files(dir_path):
    files = os.listdir(dir_path + "\\media")

    for i in files:
        calculate_md5(dir_path + "\\media", i)
        calculate_sha1(dir_path + "\\media", i)
    if not os.path.exists(dir_path + "\\thumbnails"):
        os.mkdir(dir_path + "\\thumbnails")

    generate_thumbs(dir_path + "\\media", dir_path + "\\thumbnails")


def generate_thumbs(video_path, output_path):
    videos = os.listdir(video_path)
    for video in videos:
        print("ffmpeg -i " + video_path + "\\" + video + " -ss 00:00:01.000 -vframes 1 " + output_path + "\\" + video + ".jpg")
        subprocess.run(["ffmpeg", "-i", video_path + "\\" + video, "-ss", "00:00:01.000", "-vframes", "1", output_path + "\\" + video + ".jpg"])

    shutil.copy("generic_thumb.png", output_path)


def generate_html(row_output):
    i = 1
    link = ""
    thumb = ""
    html_page.append("<tr>")
    for x in row_output:
        if x in md5:
            link = "media\\" + md5[x]
            if os.path.exists(working_path + "\\thumbnails\\" + md5[x] + ".jpg"):
                thumb = "thumbnails\\" + md5[x] + ".jpg"
            else:
                thumb = "thumbnails\\generic_thumb.png"

    html_page.append("<td>" + str(row_output[0]) + "</td>")
    html_page.append("<td><a href='" + link + "' /><img width=\"100\" height=\"100\" src='" + thumb + "' /></a></td>")

    while i < len(row_output):
        res = check_value(row_output[i])
        html_page.append("<td>" + res + "</td>")
        i += 1
    html_page.append("</tr>")


def check_value(inputted_value):
    if str(inputted_value).isdigit():
        number = int(inputted_value)
        result = f"{number:,}"
    elif inputted_value.replace('.', '', 1).isdigit() and 2 > inputted_value.count('.') > 0:
        result = str(timedelta(seconds=float(inputted_value)))
    else:
        result = inputted_value

    return result


def calculate_md5(filepath, filename):
    with open(filepath + "\\" + filename, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    md5[file_hash.hexdigest().upper()] = filename


def calculate_sha1(filepath, filename):
    with open(filepath + "\\" + filename, "rb") as f:
        file_hash = hashlib.sha1()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    sha1[file_hash.hexdigest().upper()] = filename



get_files(working_path)

for file in os.listdir(working_path):
    if file.endswith(".csv"):
        working_title = Path(file).stem
        csv = file

column_headers = create_tables(working_path + "\\" + csv)

initialize_table(html_page, name, case_num, item_num, working_title, column_headers)

c.execute("SELECT * FROM 'griffeye'")
output = c.fetchall()
for row in output:
    generate_html(row)

# print(html_page)

with open(working_path + "\\Results-formatted.html", "w") as wf:
    for lines in html_page:
        wf.write(lines)
    wf.write("</table></div></body></html>")

conn.close()