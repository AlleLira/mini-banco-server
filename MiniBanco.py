import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import winsound
import os, sys
import secrets

# ============== SOM ===============

def recurso(nome):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, nome)
    return os.path.join(os.path.dirname(__file__),nome)

def tocar_som():
    try:
        winsound.PlaySound("caixa.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    except:
        pass



# ================== DB =============

def conectar():
    return sqlite3.connect("banco.db")

def init_db():
    with conectar() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            saldo REAL,
            token TEXT UNIQUE
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            origem INTEGER,
            destino INTEGER,
            valor REAL,
            data TEXT
        )""")
        con.commit()

def obter_usuarios():
    with conectar() as con:
        return con.execute(
            "SELECT id, nome, saldo FROM usuarios ORDER BY nome"
        ).fetchall()
    
def obter_nome(uid):
    if uid is None:
        return "BANCO"
    with conectar() as con:
        return con.execute(
            "SELECT nome FROM usuarios WHERE id=?", (uid,)
        ).fetchone()[0]

def atualizar_saldo(uid, valor):
    with conectar() as con:
        con.execute(
            "UPDATE usuarios SET saldo = saldo + ? WHERE id=?",
            (valor, uid)
        )
        con.commit()

def registrar_transacao(tipo, origem, destino, valor):
    with conectar() as con:
        con.execute("""
        INSERT INTO transacoes(tipo, origem, destino, valor, data)
        VALUES (?,?,?,?,?)
        """,(
            tipo,
            origem,
            destino,
            valor,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ))
        con.commit()

# =============== FORMATO ===========

def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============ INTERFACE ================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Banco 2.0")
        self.root.geometry("420x600")
        self.root.configure(bg="#020617")
        self.menu()

    def limpar(self):
        for w in self.root.winfo_children():
            w.destroy()

    def titulo(self, texto):
        tk.Label(
            self.root,
            text=texto,
            bg="#020617",
            fg="white",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=20)
    
    def botao(self, texto, comando, parent=None, cor="#2563eb"):
        if parent is None:
            parent = self.root

        tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=cor,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            height=2
        ).pack(fill="x", padx=20, pady=6)

# ================== MENU =================

    def menu(self):
        self.limpar()

        tk.Label(
            self.root,
            text="🏦 Mini Banco 2.0",
            bg="#020627",
            fg="white",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=15)

        container = tk.Frame(self.root, bg="#020627")
        container.pack(fill="both", expand=True, padx=10)

    # ================= COLUNA BANCO ============

        frame_banco = tk.Frame(container, bg="#020617")
        frame_banco.pack(side="left", fill="both", expand=True)

        tk.Label(
            frame_banco,
            text="BANCO",
            bg="#020617",
            fg="#38bdf8",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        self.botao("Cadastrar Jogadores", self.cadastro, frame_banco)
        self.botao("Pagar Jogador", self.banco_para_usuario, frame_banco)
        self.botao("RESETAR DADOS", self.resetar, frame_banco, "#dc2626")

    # ================ COLUNA JOGADORES ============

        frame_jogadores = tk.Frame(container, bg="#020617")
        frame_jogadores.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(
            frame_jogadores,
            text="JOGADORES",
            bg="#020617",
            fg="#22c55e",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        for uid, nome, saldo in obter_usuarios():
            self.botao(
                f"{nome} | {formatar_reais(saldo)}",
                lambda u=uid: self.menu_jogador(u),
                frame_jogadores
            )

        

    # ============= FUNÇOES DO JOGO ===========
    # ====== CADASTRO ======

    def cadastro(self):
        self.limpar()
        self.titulo("Cadastrar Jogador")

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        nome =tk.Entry(frame, font=("Segoe UI",14))
        nome.pack(padx=40, pady=10)

        saldo = tk.Entry(frame, font=("Segoe UI", 14))
        saldo.pack()

        erro = tk.Label(frame, bg="#020617", fg="#ef4444")
        erro.pack()

        def salvar():
            try:
                n = nome.get().strip()
                v = float(saldo.get().replace(",", "."))
                token = secrets.token_urlsafe(32)

                if not n or v < 0:
                    raise ValueError
                
                with conectar() as con:
                    con.execute(
                        "INSERT INTO usuarios (nome, saldo, token) VALUES (?,?,?)",
                        (n, v, token)
                    )
                    con.commit()

                self.root.unbind("<Return>")
                self.menu()

            except sqlite3.IntegrityError:
                erro.config(text="Jogador já existe.")
            except ValueError:
                erro.config(text="Saldo inválido.")
            except Exception as e:
                erro.config(text=f"Erro: {e}")

        nome.focus()
        self.root.bind("<Return>", lambda e: salvar())

        self.botao("Salvar", salvar, frame)
        self.botao("Voltar", self.menu, frame, "#475569")

    # ========== VALOR =======

    def pedir_valor(self, callback):
        self.limpar()
        self.titulo("Digite o valor:")

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        entrada = tk.Entry(
            frame,
            font=("Segoe UI", 16),
            justify="center"
        )
        entrada.pack(padx=40, pady=20)

        erro = tk.Label(frame, bg="#020617", fg="#ef4444")
        erro.pack()

        def confirmar():
            texto = entrada.get().replace(",",".").strip()

            try:
                valor = float(texto)
            except ValueError:
                erro.config(text="Digite um número válido")
                return
            
            if valor <= 0:
                erro.config(text="O valor deve ser maior que zero.")
                return
            
            self.root.unbind("<Return>")
            callback(valor)
        
        entrada.focus()
        self.root.bind("<Return>", lambda e: confirmar())

        self.botao("Confirmar", confirmar, frame)
        self.botao("Voltar", self.menu, frame, "#475569")

    # ========== MENU JOGADOR =============

    def menu_jogador(self, jogador_id):
        self.limpar()
        nome = obter_nome(jogador_id)
        with conectar() as con:
            token = con.execute(
                "SELECT token FROM usuarios WHERE id=?",
                (jogador_id,)
            ).fetchone()[0]
            
        self.titulo(nome)

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        self.botao(
            "Pagar ao Banco",
            lambda: self.pedir_valor(
                lambda v: self.executar_transacao(
                    "Jogador -> Banco", jogador_id, None, v)
            ),
            frame
        )

        self.botao(
            "Pagar para Jogador",
            lambda: self.selecionar_destino("Jogador -> Jogador", jogador_id),
            frame
        )

        self.botao(
            "Extrato",
            lambda: self.mostrar_extrato(jogador_id),
            frame,
            "#16a34a"
        )

        self.botao("voltar", self.menu, frame, "#475569")
# ================== LISTAR JOGADORES =========
    def lista_jogadores(self):
        self.limpar()
        self.titulo("Jogadores")

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        for uid, nome, saldo in obter_usuarios():
            self.botao(
                f"{nome} | {formatar_reais(saldo)}",
                lambda u=uid: self.menu_jogador(u),
                frame
            )
        
        self.botao("Voltar", self.menu, frame, "#475569")

    # ============= TRANSAÇÕES ====================

    def banco_para_usuario(self):
        self.limpar()
        self.titulo("Banco -> Jogador")

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        for uid, nome, _ in obter_usuarios():
            self.botao(
                nome, lambda u=uid: self.pedir_valor(
                    lambda v: self.executar_transacao(
                        "Banco -> Jogador", None, u, v
                    )
                ),
                frame
            )

        self.botao("Voltar", self.menu, frame, "#475569")


    def usuario_para_banco(self):
        self.limpar()
        self.titulo("Jogador -> Banco")

        for uid, nome, _ in obter_usuarios():
            self.botao(
                nome,
                lambda u=uid: self.pedir_valor(
                    lambda v: self.executar_transacao(
                        "Jogador -> Banco", u, None, v
                    )
                )
            )

        self.botao("Voltar", self.menu, "#475569")
    
    def usuario_para_usuario(self):
        self.selecionar_origem("Jogador -> Jogador")
    
    def selecionar_origem(self, tipo):
        self.limpar()
        self.titulo("Quem vai pagar?")

        for uid, nome, _ in obter_usuarios():
            self.botao(
                nome, lambda u=uid: self.selecionar_destino(tipo, u)
            )
        self.botao("Voltar", self.menu, "#475569")

    def selecionar_destino(self, tipo, origem):
        self.limpar()
        self.titulo("Quem vai receber?")

        frame = tk.Frame(self.root, bg="#020617")
        frame.pack(fill="both", expand=True)

        for uid, nome, _ in obter_usuarios():
            if uid == origem:
                continue

            self.botao(
                nome,
                lambda u=uid: self.pedir_valor(
                    lambda v: self.executar_transacao(
                        tipo, origem, u, v
                    )
                ),
                frame
            )
        
        self.botao("Voltar", lambda: self.menu_jogador(origem), frame,  "#475569")
    
    def executar_transacao(self, tipo, origem, destino, valor):
        if origem:
            with conectar() as con:
                saldo = con.execute(
                    "SELECT saldo FROM usuarios WHERE id=?", (origem,)
                ).fetchone()[0]

            if saldo < valor:
                messagebox.showerror("SALDO INSUFICIENTE!")
                self.menu()
                return
            
            atualizar_saldo(origem, -valor)

        if destino:
            atualizar_saldo(destino, valor)
        
        registrar_transacao(tipo, origem, destino, valor)
        tocar_som()
        self.menu()
    
    # ==================== EXTRATO ===========

    def extrato(self):
        self.limpar()
        self.titulo("Extrato")

        self.botao("Voltar", self.menu, self.root, "#475569")

        for uid, nome, _ in obter_usuarios():
            self.botao(nome, lambda u=uid: self.mostrar_extrato(u))

    def mostrar_extrato(self, uid):
        self.limpar()
        nome = obter_nome(uid)

        with conectar() as con:
            saldo = con.execute(
                "SELECT saldo FROM usuarios WHERE id=?", (uid,)
            ).fetchone()[0]

            dados = con.execute("""
            SELECT tipo, origem, destino, valor, data
            FROM transacoes
            WHERE origem=? OR destino=?
            ORDER BY id DESC
            LIMIT 5
            """, (uid, uid)).fetchall()
        self.botao("Voltar", lambda: self.menu_jogador(uid),self.root, "#475569")
        self.titulo(nome)

        tk.Label(
            self.root,
            text=f"Saldo atual: {formatar_reais(saldo)}",
            bg="#020617",
            fg="#22c55e",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        for t, o, d, v, data in dados:
            texto = f"{data}\n{obter_nome(o)} -> {obter_nome(d)}\nR$ {v:.2f}"
            tk.Label(
                self.root,
                text=texto,
                bg="#020617",
                fg="white",
                justify="left"
            ).pack(fill="x", padx=20, pady=6)
    
# =============== RESETE ==================

    def resetar(self):
        if messagebox.askyesno("Confirmação","Apagar TODOS os dados?"):
            with conectar() as con:
                con.execute("DELETE FROM usuarios")
                con.execute("DELETE FROM transacoes")
                con.commit()
            self.menu()

# ======== MAIN =======================

init_db()
root= tk.Tk()
App(root)
root.mainloop()