#servidor TCP responsavel por receber conexoes e atender varios clientes simultaneamente
#cada cliente e atendido em uma thread separada
# usa: protocol.py: comunicacao | storage.py: arquivos | database.py: banco de dados


import socket
import threading

import protocol
import storage
import database

HOST = "0.0.0.0"
PORT = 5000
LIMITE_UPLOAD = storage.TAMANHO_MAXIMO 
USUARIO_PADRAO = "anonimo" 


def limpar_motivo(texto):
    return str(texto).replace("|", "/").replace("\r", " ").replace("\n", " ")


def erro(conn, motivo):
    protocol.enviar_linha(conn, protocol.montar("ERRO", limpar_motivo(motivo)))


def ok(conn, *campos):
    protocol.enviar_linha(conn, protocol.montar("OK", *campos))


def usuario_valido(usuario):
    if not usuario or usuario in (".", "..") or len(usuario) > 50:
        return False
    return not any(c in usuario for c in "/\\\x00")


def cmd_login(conn, partes):
    if len(partes) != 3 or not partes[1] or not partes[2]:
        erro(conn, "uso: LOGIN|usuario|senha")
        return None

    usuario, senha = partes[1], partes[2]
    if not usuario_valido(usuario) or usuario == USUARIO_PADRAO:
        erro(conn, "nome de usuario invalido")
        return None

    if database.usuario_existe(usuario):
        if not database.senha_confere(usuario, senha):
            erro(conn, "senha incorreta")
            return None
        ok(conn, "bem-vindo de volta, " + usuario)
    else:
        try:
            database.cadastrar_usuario(usuario, senha)
        except Exception:
            if not database.senha_confere(usuario, senha):
                erro(conn, "senha incorreta")
                return None
            ok(conn, "bem-vindo de volta, " + usuario)
        else:
            ok(conn, "usuario cadastrado, " + usuario)

    database.registrar_acao(usuario, "LOGIN")
    return usuario


def cmd_upload(conn, partes, usuario):
    if len(partes) != 3:
        erro(conn, "uso: UPLOAD|nome|tamanho")
        return

    try:
        tamanho = int(partes[2])
    except ValueError:
        erro(conn, "tamanho invalido")
        return


    try:
        nome = storage.limpar_nome(partes[1])
    except ValueError:
        erro(conn, "nome do arquivo invalido")
        return
    if not storage.extensao_valida(nome):
        erro(conn, "extensao de imagem nao permitida")
        return
    if tamanho <= 0:
        erro(conn, "arquivo vazio")
        return
    if tamanho > LIMITE_UPLOAD:
        erro(conn, "arquivo maior que 20 MB")
        return

    ok(conn, "pode enviar")


    dados = protocol.receber_exato(conn, tamanho)


    if not storage.eh_imagem(dados):
        erro(conn, "o arquivo nao e uma imagem valida")
        return

    if database.imagem_existe(storage.gerar_id(dados)):
        erro(conn, "essa imagem ja foi enviada")
        return

    try:
        id_img, nome, tamanho, caminho, caminho_thumb = storage.salvar_imagem(usuario, nome, dados)
    except ValueError as e:
        erro(conn, e)
        return

    database.registrar_imagem(id_img, nome, usuario, tamanho, caminho, caminho_thumb)
    database.registrar_acao(usuario, "UPLOAD", id_img)
    ok(conn, id_img)


def cmd_list(conn, usuario):
    imagens = database.listar_imagens()
    ok(conn, len(imagens))  
    for id_img, nome, autor, data, tamanho in imagens:
        protocol.enviar_linha(conn, protocol.montar(id_img, nome, autor, data, tamanho))
    database.registrar_acao(usuario, "LIST")


def cmd_baixar(conn, partes, usuario, miniatura):
    acao = "VIEW" if miniatura else "DOWNLOAD"
    if len(partes) != 2 or not partes[1]:
        erro(conn, "uso: " + acao + "|id ou nome")
        return

    imagem = database.buscar_imagem(partes[1])  # (id, nome, caminho, caminho_thumb) ou None
    if imagem is None:
        erro(conn, "imagem nao encontrada")
        return

    id_img, nome, caminho, caminho_thumb = imagem
    try:
        dados = storage.ler_arquivo(caminho_thumb if miniatura else caminho)
    except OSError:
        erro(conn, "arquivo nao encontrado no disco")
        return

    # VIEW sempre entrega JPEG; informar uma extensão .jpg mantém nome e
    # conteúdo coerentes no arquivo salvo pelo cliente.
    nome_envio = id_img + ".jpg" if miniatura else nome
    ok(conn, len(dados), nome_envio)
    protocol.enviar_arquivo(conn, dados)
    database.registrar_acao(usuario, acao, id_img)


def cmd_hist(conn):
    acoes = database.ultimas_acoes(20)
    ok(conn, len(acoes))
    for data, quem, acao, id_img in acoes:
        protocol.enviar_linha(conn, protocol.montar(data, quem, acao, id_img or ""))


def atender(conn, addr):
    print(f"Cliente conectado: {addr}")
    usuario = USUARIO_PADRAO
    try:
        while True:
            linha = protocol.receber_linha(conn)
            if not linha:
                continue
            partes = linha.split("|")
            comando = partes[0].upper()

            if comando == "LOGIN":
                nome = cmd_login(conn, partes)
                if nome:
                    usuario = nome
            elif comando == "UPLOAD":
                cmd_upload(conn, partes, usuario)
            elif comando == "LIST":
                cmd_list(conn, usuario)
            elif comando == "DOWNLOAD":
                cmd_baixar(conn, partes, usuario, miniatura=False)
            elif comando == "VIEW":
                cmd_baixar(conn, partes, usuario, miniatura=True)
            elif comando == "HIST":
                cmd_hist(conn)
            elif comando == "SAIR":
                ok(conn, "ate mais")
                break
            else:
                erro(conn, "comando desconhecido")
    except (ConnectionError, OSError):
        pass
    except Exception as e:
        print(f"Erro com {addr}: {e}")
        try:
            erro(conn, "erro interno do servidor")
        except OSError:
            pass
    finally:
        conn.close()
        print(f"Cliente desconectado: {addr}")


def main():
    database.criar_tabelas()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"Servidor iniciado na porta {PORT}")

    while True:
        conn, addr = servidor.accept()
        threading.Thread(target=atender, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
