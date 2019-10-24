import json
import hashlib
from virus_total_apis import PublicApi as VirusTotalPublicApi
from threading import Timer
import subprocess as sub
from datetime import datetime
import sys
import shlex
import subprocess
import os
import time
from ipaddress import ip_address
import requests
from urllib.request import urlopen
    
from reportlab.platypus import SimpleDocTemplate, Paragraph, Indenter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

import io


# VirusTotal API key
API_KEY = 'b39784fc9020421672ba8a46b5aa069dbf25b733b9754fccbc1d296506060a5b'
# An URL for Google Safe Browsing API
GOOGLE_URL = 'https://sb-ssl.google.com/safebrowsing/api/lookup?client=demo-app&key=AIzaSyCizNzsav3wKsOtEQ8TjL7sWzbkQo8NsWc&appver=1.5.2&pver=3.1&url={url}'

is_safe = 0

input_data = input('Please enter the IP of a machine\n')

try:
    ip_address(input_data)
except ValueError:
    print('IP address is not valid')
    sys.exit()

vt = VirusTotalPublicApi(API_KEY)
return_data = dict()

try: 
    with open('servers.txt') as f:
        logins = f.readlines()
    logins = [x.strip() for x in logins]
except IOError:
    print('Servers file doesnt exist')
    servers = None

if logins:
    for i, j in enumerate(logins):
        if input_data in logins[i]:
            login = logins[i+1][6:]
            passwd = logins[i+2][6:]
else:
    login = None
    passwd = None

if login:
    print('------------------------------------------------------')
    print('Starting scp')
    cmd= "sudo sshpass -p '"+passwd+"' scp -q -r "+login+"@"+input_data+":/var/www /home/snort/netsecurity_tool/files"
    args = shlex.split(cmd)
    scp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(.5)

    hashes = []
    files = []
    
    for root, directories, filenames in os.walk('/home/snort/netsecurity_tool/files/'): 
        for name in filenames:
            files.append(name)
            FileName = (os.path.join(root, name))
    
            hasher = hashlib.md5()
            with open(str(FileName), 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
                hashes.append(hasher.hexdigest())
    
    if not hashes:
        print('SCP: No files downloaded')
    
    if hashes:
        print(str(len(files))+' files downloaded')
    
    cmd= "sudo rm -r /home/snort/netsecurity_tool/files"
    args = shlex.split(cmd)
    rm = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    print('------------------------------------------------------')
    print('VirusTotal response')
    
    for x in range(0, len(hashes)):
      print(hashes[x])
      print('File: '+files[x])
      positives = 0
      try: 
          response = vt.get_file_report(hashes[x])
          if "not among the finished, queued or pending scans" not in response['results'].get('verbose_msg'): 
              print(response['results'].get('verbose_msg'))
              print('More analysis with links can be found via: ' + response['results']['permalink'])
              print(response['results'].get('positives'))
              for res in response['results']['scans']:
                  detected = response['results']['scans'][res]['detected']
                  if detected:
                      positives +=1
              if positives > 0:
                  print('Virus positives detected')
                  is_safe += 1
              else:
                  print('No virus detected')
              return_data['virus_total_files'] = response
          else:
              print(response['results'].get('verbose_msg'))
              print('file not in virustotal database (most likely not a virus, just a random file)')
      except:
          print('An error with VirusTotal has occured. Skipping scan with VirusTotal')
          return_data['virus_total_files'] = 'An error with VirusTotal has occured.'
      print('15 second delay')
      time.sleep(15)
else:
    print('skipping scp scan')

print('------------------------------------------------------')
print('VirusTotal response')
try:
    response = vt.scan_url(this_url='http://' + input_data)
    print(response['results'].get('verbose_msg'))
    print('More analysis with links can be found via: ' + response['results']['permalink'])
    return_data['virus_total'] = response
except:
    print('An error with VirusTotal has occured. Skipping scan with VirusTotal')
    return_data['virus_total'] = 'An error with VirusTotal has occured.'
	
print('------------------------------------------------------')
print('Google Safe Browsing response')
gglbr_response = urlopen(GOOGLE_URL.format(url=input_data)).read().decode("utf8")
if gglbr_response != 'malware':
    print('Google Safe Browsing result - Safe')
    return_data['google_safe_browsing'] = 'safe'
else:
    is_safe += 1 
    print('Google Safe Browsing result - UNSAFE!!!')
    return_data['google_safe_browsing'] = 'unsafe'
	
print('------------------------------------------------------')
print('NMAP response')
nmap = sub.Popen(('nmap', '-sV', '--script', 'http-malware-host', input_data), stdout=sub.PIPE)
# https://nmap.org/nsedoc/scripts/http-malware-host.html
nmap_data = []
nmap_found_risk = False
for row in iter(nmap.stdout.readline, b''):
    nmap_data.append(row.rstrip().decode('utf-8'))
    if 'infected' in row.rstrip().decode('utf-8'):
        nmap_found_risk = True
    print(row.rstrip().decode('utf-8'))
if nmap_found_risk:
    is_safe += 1
return_data['nmap'] = nmap_data


print('------------------------------------------------------')
print('TCPDUMP response')
cmd = "sudo tcpdump -l -v -n dst host not " + input_data + " and dst port 80"
# https://lxadm.com/Using_tcpdump_to_detect_malware_presence
args = shlex.split(cmd)
tcpdump = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print ("Press CTRL-C to stop tcpdump")
output = io.StringIO()
running = True
start_time = time.time()
while running:
    try:
        data = tcpdump.stdout.readline()
        print(data.decode('utf-8'))
        if len(data):
            output.write(data.decode('utf-8'))
        else:
            running = False
        if time.time() - start_time >= 10.0:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        os.system("sudo kill %s" % (tcpdump.pid,))
        data = tcpdump.stdout.readline()
        if len(data):
            output.write(data.decode('utf-8'))
        running = False

lines = output.getvalue().split("\n")
tcp_data = []
for i, line in enumerate(lines):
    if line:
        tcp_data.append("{0} => {1}".format(i, line))
return_data['tcp'] = tcp_data
	
filename = 'reports/' + datetime.now().strftime('%Y%m%d%H%M') + '.pdf'
#with open('reports/'+filename, 'a') as report:
#    report.write(json.dumps(return_data, sort_keys=False, indent=4) + '\r\n')
    

buf = io.BytesIO()


doc = SimpleDocTemplate(
    buf,
    rightMargin=inch/2,
    leftMargin=inch/2,
    topMargin=inch/2,
    bottomMargin=inch/2,
    pagesize=letter,
)

styles = getSampleStyleSheet()

paragraphs = []
for key, value in return_data.items():
    indent = ParagraphStyle("ingredent", leftIndent=20)  
    if key == 'tcp':
        paragraphs.append(Paragraph('TCPDUMP response:', styles['Normal']))
        if len(value) < 2:
            paragraphs.append(Paragraph('No redirects has been spotted or the listening has been interrupted', indent))
        else:
            for val in value:
                paragraphs.append(Paragraph(val, indent))
    elif key == 'nmap':
        paragraphs.append(Paragraph('NMAP response:', styles['Normal']))
        for val in value:
            paragraphs.append(Paragraph(val, indent))
    elif key == 'virus_total':
        paragraphs.append(Paragraph('VirusTotal URL scan results:', styles['Normal']))
        for k, v in value.items():
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    paragraphs.append(Paragraph(str(k1) + ': ' + str(v1), indent))
            else:
                paragraphs.append(Paragraph(str(k) + ': ' + str(v), indent))
    elif key == 'google_safe_browsing':
        paragraphs.append(Paragraph('Google Safe Browsing results:', styles['Normal']))
        paragraphs.append(Paragraph(value, indent))      
    elif key == 'virus_total_files':
        paragraphs.append(Paragraph('VirusTotal files scan results:', styles['Normal']))
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, dict):
                    for k1, v1 in v.items():
                        if isinstance(v1, dict):
                            paragraphs.append(Paragraph('scans: ', indent))
                            indent2 = ParagraphStyle("ingredent", leftIndent=40)
                            for k2, v2 in v1.items():
                                if isinstance(v2, dict):
                                    paragraphs.append(Paragraph('--------', indent2))
                                    for k3, v3 in v2.items():
                                       paragraphs.append(Paragraph(str(k3) + ': ' + str(v3), indent2))
                                    paragraphs.append(Paragraph('--------', indent2))
                                else:
                                    paragraphs.append(Paragraph(str(k2) + ': ' + str(v2), indent2))
                        
                else:
                    paragraphs.append(Paragraph(str(k) + ': ' + str(v), indent))
        else:
            paragraphs.append(Paragraph(value, indent))
    
doc.build(paragraphs)


with open(filename, 'w') as fd:
    fd.write(buf.getvalue().decode('windows-1252'))
    
    
    
print('Report has been saved in reports folder as ' + filename)
print('Scan has been successful')
if is_safe:
    print('There were some risks found. Please examine the report for further analysis')
else:
    print('From the first scan, everything looks pretty safe. For further investigation, please analyse TCPDUMP response and VirusTotal generated report on permalink.')
