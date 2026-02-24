from flask import Flask
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


@app.route("/")
def mostrar_cotacoes():
    resultados = [pegar_cotizaciones(url) for url in urls]

    # Melhores valores
    dolar_validos = [r for r in resultados if r['dolar_real_venta'] is not None]
    real_validos = [r for r in resultados if r['real_guarani_compra'] is not None]

    melhor_dolar = min(dolar_validos, key=lambda x: x['dolar_real_venta']) if dolar_validos else None
    melhor_guarani = max(real_validos, key=lambda x: x['real_guarani_compra']) if real_validos else None

    texto = """
    <html>
    <head>
        <title>🤘La moneda Portable🤘</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0b0b0b; color: #cfcfcf; padding: 20px; margin: 0; }
            h1 { text-align: center; color: #d0d0d0; margin-bottom: 30px; font-weight: 500; letter-spacing: 1px; }
            table { width: 90%; margin: auto; border-collapse: collapse; background-color: #121212; border-radius: 10px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.6); }
            th, td { padding: 14px; text-align: center; }
            th { background: #1a1a1a; color: #9a9a9a; font-weight: 500; border-bottom: 1px solid #2a2a2a; }
            td { border-bottom: 1px solid #1f1f1f; font-size: 15px; color: #cfcfcf; }
            tr:hover { background-color: #181818; }
            .melhor { background-color: #1b2b1b !important; color: #9be79b; font-weight: bold; }
            caption { font-size: 20px; margin: 15px; color: #b5b5b5; font-weight: 500; }
            footer { text-align: center; margin-top: 20px; color: #777; font-size: 13px; }
        </style>
    </head>
    <body>
        <h1>🤘La moneda🤘</h1>
        <table>
            <caption>Cotações por Sucursal</caption>
            <tr>
                <th>Sucursal</th>
                <th>Data</th>
                <th>Dólar (Venda)</th>
                <th>Guarani (Compra)</th>
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

    texto += """
        </table>
        <footer>Atualizado automaticamente • BY JOVICUNHA</footer>
    </body>
    </html>
    """

    return texto


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)