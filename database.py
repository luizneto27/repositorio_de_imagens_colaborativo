# Registrar usuários, arquivos e histórico

import sqlite3
import hashlib
import threading
import os
from datetime import datetime

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(PASTA, "repository.db")

# o servidor tem uma thread por cliente, entao so uma pode mexer no banco por vez
trava = threading.Lock()


def conectar():
    return sqlite3.connect(ARQUIVO_DB)


def agora():
    # nesse formato ordenar como texto ja ordena por data
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def criar_tabelas():
    with trava:
        con = conectar()
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            nome TEXT PRIMARY KEY,
            senha_hash TEXT NOT NULL,
            criado_em TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS imagens (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            autor TEXT NOT NULL,
            tamanho INTEGER,
            data_envio TEXT,
            caminho TEXT,
            caminho_thumb TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            usuario TEXT,
            acao TEXT,
            imagem_id TEXT
        )""")
        con.commit()
        con.close()


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def usuario_existe(nome):
    with trava:
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT nome FROM usuarios WHERE nome = ?", (nome,))
        linha = cur.fetchone()
        con.close()
    return linha is not None


def cadastrar_usuario(nome, senha):
    with trava:
        con = conectar()
        cur = con.cursor()
        cur.execute("INSERT INTO usuarios (nome, senha_hash, criado_em) VALUES (?, ?, ?)",
                    (nome, hash_senha(senha), agora()))
        con.commit()
        con.close()


def senha_confere(nome, senha):
    with trava:
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT senha_hash FROM usuarios WHERE nome = ?", (nome,))
        linha = cur.fetchone()
        con.close()
    if linha is None:
        return False
    return linha[0] == hash_senha(senha)
