### PREFERRED MODE

# To visualize <177435615773235.html>:

1. Go to the bff_browser directory:
   cd beacon2-cbi-tools/utils/bff_browser

2. Start the BFF Browser Flask App:
   python3 app.py

3. Open your browser and navigate to:
   http://0.0.0.0:8001/

4. Follow the instructions on the Home page.

---

### ALTERNATIVE MODES

# Option 1: Open <177435615773235.html> directly in Chromium
chromium --allow-file-access-from-files --disable-web-security 177435615773235.html

# Option 2: Use an HTTP server. Example using Python 3:
python3 -m http.server
