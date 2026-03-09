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
    except:
        return {"sucursal":"Erro","fecha":"-","dolar_real_venta":None,"real_guarani_compra":None}

def formatar_brl(valor):
    try:
        return f"G$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return str(valor)

@app.route("/", methods=["GET","POST"])
def mostrar_cotacoes():
    resultados = [pegar_cotizaciones(url) for url in urls]
    dolar_validos = [r for r in resultados if r['dolar_real_venta']]
    real_validos = [r for r in resultados if r['real_guarani_compra']]
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
        except:
            valor = None

    texto = f"""
<html>
<head>
<title>🤘Nosso PY🤘</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<style>
/* ===== FUNDO QUE ROLA NORMAL ===== */
body {{
    margin:0;
    padding:0;
    font-family:'Segoe UI',sans-serif;
    color:#f0f0f0;

    /* fundo que rola por baixo dos elementos */
    background: url('https://i.imgur.com/CmpkqDh.jpeg') center top / cover no-repeat;
    background-attachment: scroll;
}}

.content {{
    padding:20px;
    min-height:200vh; /* garante scroll suficiente */
}}

h1 {{text-align:center;margin-bottom:30px;font-size:2.3em;}}
form {{text-align:center;margin:30px auto;display:flex;justify-content:center;gap:10px;flex-wrap:wrap;}}
input[type=number],input[type=submit]{{padding:12px 20px;border-radius:8px;border:none;font-size:16px;}}
input[type=number]{{background:rgba(30,30,30,0.8);color:#fff;width:200px;}}
input[type=submit]{{background:#000;color:#fff;cursor:pointer;}}
.resultado {{margin-top:20px;text-align:center;font-size:1.2em;}}
table {{width:90%;margin:30px auto;border-collapse:collapse;background:rgba(20,20,20,0.85);border-radius:12px;overflow:hidden;}}
th,td {{padding:14px;text-align:center;}}
th {{background:rgba(0,0,0,0.6);}}
td {{border-bottom:1px solid rgba(255,255,255,0.1);}}
.melhor {{color:#2ecc71;font-weight:bold;}}
.video-container {{width:90%;max-width:900px;margin:40px auto;text-align:center;}}
video {{width:100%;border-radius:12px;}}
footer {{text-align:center;margin-top:40px;color:#aaa;}}
</style>
</head>
<body>
<div class="content">
<h1>🤘Nosso PY🤘</h1>

<form method="POST">
<input type="number" name="valor" placeholder="Converter real" value="{valor if valor else ''}" step="any" min="0" required>
<input type="submit" value="Calcular">
</form>

<div class='resultado'>
"""
    if valor:
        if resultado_dolar:
            texto += f"💵 Dólares: U$ {resultado_dolar:.2f}<br>"
        if resultado_guarani:
            texto += f"💴 Guarani: {formatar_brl(resultado_guarani)}<br>"
    texto += "</div>"

    texto += "<table><tr><th>Sucursal</th><th>Data</th><th>Dólar</th><th>Guarani</th></tr>"
    for res in resultados:
        classe_dolar = "melhor" if melhor_dolar and res['sucursal']==melhor_dolar['sucursal'] else ""
        classe_guarani = "melhor" if melhor_guarani and res['sucursal']==melhor_guarani['sucursal'] else ""
        texto += f"<tr><td>{res['sucursal']}</td><td>{res['fecha']}</td><td class='{classe_dolar}'>{res['dolar_real_venta']}</td><td class='{classe_guarani}'>{res['real_guarani_compra']}</td></tr>"
    texto += "</table>"

    # Vídeos
    for idx,(titulo,src) in enumerate([
        ("📹 PY ➡️ FOZ","https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidobrasil.stream/chunklist_w1853171642.m3u8"),
        ("📹 FOZ ➡️ PY","https://video04.logicahost.com.br/portovelhomamore/fozpontedaamizadesentidoparaguai.stream/chunklist_w1130272214.m3u8")
    ],1):
        texto += f"""
<div class='video-container'>
<h2>{titulo}</h2>
<video id='video{idx}' controls autoplay muted playsinline></video>
</div>
<script>
var video{idx} = document.getElementById('video{idx}');
if(Hls.isSupported()) {{
    var hls = new Hls();
    hls.loadSource('{src}');
    hls.attachMedia(video{idx});
}} else if(video{idx}.canPlayType('application/vnd.apple.mpegurl')) {{
    video{idx}.src='{src}';
}}
</script>
"""

    texto += "<footer>Atualizado automaticamente • BY JOVICUNHA</footer></div></body></html>"

    return texto

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
