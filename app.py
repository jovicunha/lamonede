from flask import Flask, request
import requests
import os

app = Flask(__name__)

urls = [
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=casa_matriz",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_jebai",
    "https://www.lamoneda.com.py/api/cotizaciones.php?sucursal=sucursal_centro"
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

    # ---------------- CALCULADORA ----------------
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
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #0b0b0b;
                color: #cfcfcf;
                padding: 20px;
                margin: 0;
            }}

            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}

            table {{
                width: 90%;
                margin: auto;
                border-collapse: collapse;
                background-color: #121212;
                border-radius: 10px;
                overflow: hidden;
            }}

            th, td {{
                padding: 14px;
                text-align: center;
            }}

            th {{
                background: #1a1a1a;
                color: #9a9a9a;
            }}

            td {{
                border-bottom: 1px solid #1f1f1f;
            }}

            tr:hover {{
                background-color: #181818;
            }}

            .melhor {{
                background-color: #1b2b1b !important;
                color: #9be79b;
                font-weight: bold;
            }}

            form {{
                text-align: center;
                margin: 30px;
            }}

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

            .resultado {{
                margin-top: 20px;
                text-align: center;
                font-size: 18px;
                color: #9be79b;
            }}

            .resultado.calculadora {{
                color: #ff6666;
            }}

            footer {{
                text-align: center;
                margin-top: 20px;
                color: #777;
                font-size: 13px;
            }}
        </style>
    </head>

    <body>
        <h1>🤘Nosso PY🤘</h1>

        <form method="POST">
            <input
                type="number"
                name="valor"
                placeholder="Converter real"
                value="{valor if valor else ''}"
                inputmode="decimal"
                step="any"
                min="0"
                required
            >
            <input type="submit" value="Calcular">
        </form>
    """

    # -------- RESULTADO CALCULADORA --------
    texto += "<div class='resultado calculadora'>"
    if valor:
        if resultado_dolar is not None:
            texto += f"💵 Dólares: U$ {resultado_dolar:.2f}<br>"
        if resultado_guarani is not None:
            texto += f"💴 Guarani: {formatar_brl(resultado_guarani)}<br>"
    texto += "</div>"

    # -------- TABELA --------
    texto += """
        <table>
            <caption>Cotações por Sucursal</caption>
            <tr>
                <th>Sucursal</th>
                <th>Data</th>
                <th>Dólar </th>
                <th>Guarani </th>
            </tr>
    """

    for res in resultados:
        classe_dolar = "melhor" if melhor_dolar and res['sucursal'] == melhor_dolar['sucursal'] else ""
        classe_guarani = "melhor" if melhor_guarani and res['sucursal'] == melhor_guarani['sucursal'] else ""

        texto += f"""
            <tr>
                <td>{res['sucursal']}</td>
                <td>{res['fecha']}</td>
                <td class="{classe_dolar}">{res['dolar_real_venta']}</td>
                <td class="{classe_guarani}">{res['real_guarani_compra']}</td>
            </tr>
        """

    texto += "</table>"

    # -------- DASHBOARD AGORA ABAIXO DA TABELA --------
    if melhor_dolar and melhor_guarani:
        texto += "<div class='resultado'>"

        aluguel = 330 * melhor_dolar['dolar_real_venta']
        texto += f"<br>🏠 Aluguel: {aluguel:.2f} R$<br>"

        conta_internet = 100000 / melhor_guarani['real_guarani_compra']
        texto += f"🌐 Conta de Internet: {conta_internet:.2f} R$<br>"

        universidade_valor = 2195000 / melhor_guarani['real_guarani_compra']
        texto += f"🎓 Universidade: {universidade_valor:.2f} R$<br>"

        texto += "</div>"

    texto += """
        <footer>Atualizado automaticamente • BY JOVICUNHA</footer>
    </body>
    </html>
    """

    return texto


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

