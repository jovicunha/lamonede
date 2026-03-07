from flask import Flask, request
import requests
import os
import threading
import time

app = Flask(__name__)

# -----------------------------
# URLs das cotações
# -----------------------------
urls = [
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=casa_matriz",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_jebai",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_centro",
    "https://www.lamoneda.com.py/api/cotizaciones?sucursal=sucursal_km7"
]

# Valor da luz (inicial)
valor_luz_global = "Carregando..."

# -----------------------------
# Função para pegar cotações
# -----------------------------
def pegar_cotizaciones(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        sucursal = data.get("sucursal", "Desconhecida")
        fecha = data.get("fecha", "Desconhecida")

        dolar_real = None
        real_guarani = None

        for cot in data.get("cotizaciones", []):
            if cot.get("moneda1") == "DOLAR" and cot.get("moneda2") == "REAL":
                dolar_real = float(cot.get("venta", 0))
            elif cot.get("moneda1") == "REAL" and cot.get("moneda2") == "GUARANI":
                real_guarani = float(cot.get("compra", 0))

        return {
            "sucursal": sucursal,
            "fecha": fecha,
            "dolar_real_venta": dolar_real,
            "real_guarani_compra": real_guarani
        }

    except requests.RequestException as e:
        return {
            "sucursal": f"Erro ({e})",
            "fecha": "-",
            "dolar_real_venta": None,
            "real_guarani_compra": None
        }

# -----------------------------
# Função para formatar Guarani
# -----------------------------
def formatar_brl(valor):
    try:
        return f"G$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return str(valor)

# -----------------------------
# Selenium para pegar todas as faturas da luz
# -----------------------------
def atualizar_luz_thread():
    global valor_luz_global
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    import time

    chrome_driver_path = "C:/Users/JVCR/OneDrive/Desktop/chromedriver-win64/chromedriver.exe"

    while True:
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            wait = WebDriverWait(driver, 20)

            driver.get("https://www.ande.gov.py/servicios/")

            mi_cuenta = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//label[@onclick=\"cambiarContainer('mi_cuenta')\"]")
                )
            )
            driver.execute_script("arguments[0].click();", mi_cuenta)

            select_doc = wait.until(
                EC.presence_of_element_located((By.ID, "in-MiCuentaLogin_tipoDocumento"))
            )
            Select(select_doc).select_by_value("TD004")

            documento = driver.find_element(By.ID, "in-MiCuentaLogin_documentoIdentificacion")
            documento.send_keys("FV678082")

            senha = driver.find_element(By.ID, "in-MiCuentaLogin_password")
            senha.send_keys("Parada23@")

            acceder = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@onclick='miCuentaComponent.login()']")
                )
            )
            driver.execute_script("arguments[0].click();", acceder)
            time.sleep(3)

            consulta = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[@onclick=\"cambiarContainer('factura_publico')\"]")
                )
            )
            driver.execute_script("arguments[0].click();", consulta)

            nis = wait.until(
                EC.presence_of_element_located((By.ID, "in-Factura_Publica_nis"))
            )
            nis.send_keys("1842987")

            consultar = driver.find_element(By.XPATH, "//button[@onclick=\"haber('1')\"]")
            driver.execute_script("arguments[0].click();", consultar)

            time.sleep(3)

            divs = driver.find_elements(By.CSS_SELECTOR, "div.card-title.h4")

            luz_list = []
            for div in divs:
                try:
                    span = div.find_element(By.CSS_SELECTOR, "span.label.h6.label-warning")
                    if "Pendiente de Pago" in span.text:
                        valor = div.text.replace(span.text, "").strip()
                        luz_list.append(valor)
                except:
                    continue

            driver.quit()

            if luz_list:
                valor_luz_global = "<br>".join(luz_list)
            else:
                valor_luz_global = "Nenhuma fatura pendente"

        except:
            valor_luz_global = "Erro ao consultar"

        time.sleep(600)  # Atualiza a cada 10 minutos

# Inicia thread da luz
threading.Thread(target=atualizar_luz_thread, daemon=True).start()

# -----------------------------
# Flask - Página principal
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def mostrar_cotacoes():

    resultados = [pegar_cotizaciones(url) for url in urls]

    dolar_validos = [r for r in resultados if r['dolar_real_venta'] is not None]
    real_validos = [r for r in resultados if r['real_guarani_compra'] is not None]

    melhor_dolar = min(dolar_validos, key=lambda x: x['dolar_real_venta']) if dolar_validos else None
    melhor_guarani = max(real_validos, key=lambda x: x['real_guarani_compra']) if real_validos else None

    valor = request.form.get("valor")
    resultado_dolar = resultado_guarani = None

    if valor:
        try:
            valor_num = float(valor.replace(",", "."))
            if melhor_dolar:
                resultado_dolar = valor_num / melhor_dolar['dolar_real_venta']
            if melhor_guarani:
                resultado_guarani = valor_num * melhor_guarani['real_guarani_compra']
        except ValueError:
            valor = None

    texto = f"""
    <html>
    <head>
        <title>🤘Nosso PY🤘</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #0b0b0b;
                color: #cfcfcf;
                padding: 20px;
                margin: 0;
            }}
            h1 {{ text-align: center; margin-bottom: 30px; }}
            table {{
                width: 90%;
                margin: auto;
                border-collapse: collapse;
                background-color: #121212;
                border-radius: 10px;
                overflow: hidden;
            }}
            th, td {{ padding: 14px; text-align: center; }}
            th {{ background: #1a1a1a; color: #9a9a9a; }}
            td {{ border-bottom: 1px solid #1f1f1f; }}
            tr:hover {{ background-color: #181818; }}
            .melhor {{ background-color: #1b2b1b !important; color: #9be79b; font-weight: bold; }}
            form {{ text-align: center; margin: 30px; }}
            input[type=number] {{
                padding: 12px;
                width: 220px;
                border-radius: 6px;
                border: none;
                font-size: 16px;
                background: #1a1a1a;
                color: #fff;
            }}
            input[type=submit] {{
                padding: 12px 22px;
                border-radius: 6px;
                border: none;
                background: #333;
                color: #9be79b;
                cursor: pointer;
            }}
            .resultado {{ margin-top: 20px; text-align: center; font-size: 18px; color: #9be79b; }}
            .resultado.calculadora {{ color: #ff6666; }}
            footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 13px; }}
        </style>
    </head>
    <body>
        <h1>🤘Nosso PY🤘</h1>

        <form method="POST">
            <input type="number" name="valor" placeholder="Converter real" value="{valor if valor else ''}" inputmode="decimal" step="any" min="0" required>
            <input type="submit" value="Calcular">
        </form>
    """

    # Calculadora
    texto += "<div class='resultado calculadora'>"
    if valor:
        if resultado_dolar is not None:
            texto += f"💵 Dólares: U$ {resultado_dolar:.2f}<br>"
        if resultado_guarani is not None:
            texto += f"💴 Guarani: {formatar_brl(resultado_guarani)}<br>"
    texto += "</div>"

    # Tabela de cotações
    texto += """
        <table>
            <caption>Cotações por Sucursal</caption>
            <tr><th>Sucursal</th><th>Data</th><th>Dólar</th><th>Guarani</th></tr>
    """
    for res in resultados:
        classe_dolar = "melhor" if melhor_dolar and res['sucursal'] == melhor_dolar['sucursal'] else ""
        classe_guarani = "melhor" if melhor_guarani and res['sucursal'] == melhor_guarani['sucursal'] else ""
        texto += f"<tr><td>{res['sucursal']}</td><td>{res['fecha']}</td><td class='{classe_dolar}'>{res['dolar_real_venta']}</td><td class='{classe_guarani}'>{res['real_guarani_compra']}</td></tr>"
    texto += "</table>"

    # Dashboard
    if melhor_dolar and melhor_guarani:
        texto += "<div class='resultado'>"
        aluguel = 330 * melhor_dolar['dolar_real_venta']
        texto += f"<br>🏠 Aluguel: {aluguel:.2f} R$<br>"
        conta_internet = 100000 / melhor_guarani['real_guarani_compra']
        texto += f"🌐 Conta de Internet: {conta_internet:.2f} R$<br>"
        universidade_valor = 2195000 / melhor_guarani['real_guarani_compra']
        texto += f"🎓 Universidade: {universidade_valor:.2f} R$<br>"
        texto += "</div>"

    # ---- LINHA DA LUZ ABAIXO DO DASHBOARD ----
    texto += f"""
    <div class='resultado'>
        ⚡ Luz:<br>{valor_luz_global}
    </div>
    """

    # Primeiro vídeo
    texto += """
    <div style="width:90%;margin:auto;margin-top:40px;text-align:center;">
        <h2>📹 PY ➡️ FOZ</h2>
        <video id="video1" controls autoplay muted playsinline style="width:100%;max-width:900px;border-radius:10px;"></video>
    </div>
    <script>
        var video1 = document.getElementById('video1');
        var videoSrc1 = "https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidobrasil.stream/chunklist_w1853171642.m3u8";
        if (Hls.isSupported()) {
            var hls1 = new Hls();
            hls1.loadSource(videoSrc1);
            hls1.attachMedia(video1);
        } else if (video1.canPlayType('application/vnd.apple.mpegurl')) {
            video1.src = videoSrc1;
        }
    </script>
    """

    # Segundo vídeo
    texto += """
    <div style="width:90%;margin:auto;margin-top:40px;text-align:center;">
        <h2>📹 FOZ ➡️ PY </h2>
        <video id="video2" controls autoplay muted playsinline style="width:100%;max-width:900px;border-radius:10px;"></video>
    </div>
    <script>
        var video2 = document.getElementById('video2');
        var videoSrc2 = "https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidoparaguai.stream/chunklist_w1130272214.m3u8";
        if (Hls.isSupported()) {
            var hls2 = new Hls();
            hls2.loadSource(videoSrc2);
            hls2.attachMedia(video2);
        } else if (video2.canPlayType('application/vnd.apple.mpegurl')) {
            video2.src = videoSrc2;
        }
    </script>
    """

    # Footer
    texto += """
        <footer>Atualizado automaticamente • BY JOVICUNHA</footer>
    </body>
    </html>
    """

    return texto

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
