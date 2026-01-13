from flask import Flask
import sqlite3

app = Flask(__name__)

def conectar():
    return sqlite3.connect("banco.db", check_same_thread=False)

def nome_usuario(uid):
    if uid is None:
        return "BANCO"
    with conectar() as con:
        dado = con.execute(
            "SELECT nome FROM usuarios WHERE id =?",
            (uid,)
        ). fetchone()
        return dado[0] if dado else "?"
    
def formatar(valor):
    return f"R$ {valor:,.2f}".replace(",","x").replace(".",",").replace("X", ".")

@app.route("/extrato/<token>")
def extrato(token):
    with conectar() as con:
        user = con.execute(
            "SELECT id, nome, saldo FROM usuarios WHERE token=?",
            (token,)
        ).fetchone()

        if not user:
            return "Link inválido", 404

        uid, nome, saldo = user

        transacoes = con.execute("""
            SELECT tipo, origem, destino, valor, data
            FROM transacoes
            WHERE origem=? OR destino=?
            ORDER BY id DESC
            LIMIT 10
        """, (uid, uid)).fetchall()

    html = f"""
    <html>
    <head>
        <title>Mini Banco</title>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial;">
        <h1>🏦 Mini Banco</h1>
        <h2>{nome}</h2>
        <h3>Saldo atual: {formatar(saldo)}</h3>
        <hr>
    """

    for t, o, d, v, data in transacoes:
        html += f"""
        <p>
        <b>{data}</b><br>
        {nome_usuario(o)} → {nome_usuario(d)}<br>
        {formatar(v)}
        </p>
        <hr>
        """
    html += "<body></html>"
    return html

if __name__ == "__main__":
        app.run
