from flask import Flask, request
import requests
import os

app = Flask(__name__)

urls = [
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=casa_matriz",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_jebai",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_centro",
    "https://www.lamoneda.com.py/api/cotizaciones?sucursal=sucursal_km7"
]

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

def formatar_brl(valor):
    try:
        return f"G$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return str(valor)

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
            /* ===== FUNDO COM IMAGEM ONLINE ===== */
            body {{
                font-family: 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
                color: #f0f0f0;
                background: url('https://i.imgur.com/l3Hc14w.jpeg') no-repeat center center scroll;
                background-size: cover;
            }}
            body::before {{
                content: "";
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                backdrop-filter: blur(4px);
                background: rgba(0,0,0,0.5);
                z-index: -1;
            }}
            h1 {{ text-align: center; margin-bottom: 30px; font-size: 2.5em; }}

            /* FORMULÁRIO */
            form {{
                text-align: center;
                margin: 30px auto;
                display: flex;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            input[type=number], input[type=submit] {{
                padding: 12px 20px;
                border-radius: 8px;
                border: none;
                font-size: 16px;
            }}
            input[type=number] {{
                background: rgba(30,30,30,0.8);
                color: #fff;
                width: 200px;
            }}
            input[type=submit] {{
                background: #000000;
                color: #ffffff;
                cursor: pointer;
                transition: 0.3s;
            }}
            input[type=submit]:hover {{
                background: #222222;
            }}

            /* RESULTADO */
            .resultado {{
                margin-top: 20px;
                text-align: center;
                font-size: 1.2em;
            }}
            .calculadora {{ color: #ffcc66; }}

            /* TABELA */
            table {{
                width: 90%;
                margin: 30px auto;
                border-collapse: collapse;
                background: rgba(20,20,20,0.85);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(0,0,0,0.5);
            }}
            th, td {{
                padding: 14px;
                text-align: center;
            }}
            th {{
                background: rgba(0,0,0,0.6);
                color: #ddd;
            }}
            td {{ border-bottom: 1px solid rgba(255,255,255,0.1); }}
            tr:hover {{ background-color: rgba(255,255,255,0.05); }}
            .melhor {{ color: #2ecc71; font-weight: bold; }}

            /* FOOTER */
            footer {{
                text-align: center;
                margin-top: 40px;
                font-size: 0.9em;
                color: #aaa;
            }}

            /* VIDEO */
            .video-container {{
                width: 90%;
                max-width: 900px;
                margin: 40px auto;
                text-align: center;
            }}
            video {{
                width: 100%;
                border-radius: 12px;
            }}

            /* ===== AJUSTE PARA IPHONE / CELULARES ===== */
            @media (max-width: 768px) {{
                body {{
                    background-position: center top;
                    padding: 10px;
                }}
                h1 {{ font-size: 2em; }}
                input[type=number] {{ width: 160px; }}
                .video-container {{ width: 100%; margin: 20px auto; }}
                table {{ width: 100%; font-size: 14px; }}
            }}
        </style>
    </head>
    <body>
        <h1>🤘Nosso PY🤘</h1>

        <form method="POST">
            <input type="number" name="valor" placeholder="Converter real" value="{valor if valor else ''}" step="any" min="0" required>
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

    # Tabela
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

    # Vídeos
    for idx, (titulo, src) in enumerate([
        ("📹 PY ➡️ FOZ", "https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidobrasil.stream/chunklist_w1853171642.m3u8"),
        ("📹 FOZ ➡️ PY", "https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidoparaguai.stream/chunklist_w1130272214.m3u8")
    ], 1):
        texto += f"""
        <div class='video-container'>
            <h2>{titulo}</h2>
            <video id='video{idx}' controls autoplay muted playsinline></video>
        </div>
        <script>
            var video{idx} = document.getElementById('video{idx}');
            if (Hls.isSupported()) {{
                var hls{idx} = new Hls();
                hls{idx}.loadSource('{src}');
                hls{idx}.attachMedia(video{idx});
            }} else if (video{idx}.canPlayType('application/vnd.apple.mpegurl')) {{
                video{idx}.src = '{src}';
            }}
        </script>
        """

    texto += """
        <footer>Atualizado automaticamente • BY JOVICUNHA</footer>
    </body>
    </html>
    """

    return texto

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
