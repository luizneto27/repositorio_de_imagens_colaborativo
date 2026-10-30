import socket
import os
import sys
import argparse
from pathlib import Path
import getpass

TAMANHO_MAXIMO = 20 * 1024 * 1024
PASTA_DOWNLOADS = Path(__file__).resolve().parent / "downloads"


# comunicação

def enviar_linha(sock, mensagem):
    mensagem = mensagem + "\n"
    sock.sendall(mensagem.encode("utf-8"))


def receber_linha(sock):
    dados = bytearray()

    while True:
        byte = sock.recv(1)

        if not byte:
            raise ConnectionError("Conexão encerrada pelo servidor.")

        if byte == b"\n":
            break

        dados.extend(byte)

    return dados.decode("utf-8")


def receber_bytes(sock, tamanho):
    dados = bytearray()

    while len(dados) < tamanho:
        bloco = sock.recv(min(4096, tamanho - len(dados)))

        if not bloco:
            raise ConnectionError("Conexão interrompida durante a transferência.")

        dados.extend(bloco)

    return bytes(dados)


def verificar_resposta(resposta):
    if resposta.startswith("ERRO|"):
        print(f"\nErro do servidor: {resposta[5:]}")
        return False

    if not resposta.startswith("OK|"):
        print(f"\nResposta inesperada do servidor: {resposta}")
        return False

    return True


# login

def fazer_login(sock):
    usuario = input("Usuário: ").strip()
    senha = getpass.getpass("Senha: ")

    if not usuario or not senha or "|" in usuario or "|" in senha:
        print("Usuário ou senha inválidos.")
        return

    enviar_linha(sock, f"LOGIN|{usuario}|{senha}")

    resposta = receber_linha(sock)

    if verificar_resposta(resposta):
        print("Login realizado com sucesso!")


# upload

def upload(sock):
    caminho = input("Caminho da imagem: ").strip().strip('"')

    if not os.path.isfile(caminho):
        print("Arquivo não encontrado.")
        return

    nome = os.path.basename(caminho)

    if not nome or "|" in nome or "\n" in nome or "\r" in nome:
        print("Nome de arquivo inválido.")
        return

    tamanho = os.path.getsize(caminho)

    if tamanho == 0:
        print("O arquivo está vazio.")
        return

    if tamanho > TAMANHO_MAXIMO:
        print("A imagem ultrapassa o limite de 20 MB.")
        return

    # envia o comando
    enviar_linha(sock, f"UPLOAD|{nome}|{tamanho}")

    # aguarda autorização do servidor
    resposta = receber_linha(sock)

    if not verificar_resposta(resposta):
        return

    # só envia os bytes se o servidor autorizar
    if resposta != "OK|pode enviar":
        print("Resposta inesperada do servidor.")
        return

    with open(caminho, "rb") as arquivo:
        while True:
            bloco = arquivo.read(4096)

            if not bloco:
                break

            sock.sendall(bloco)

    # aguarda resultado do armazenamento
    resposta = receber_linha(sock)

    if verificar_resposta(resposta):
        partes = resposta.split("|", 1)

        if len(partes) == 2:
            print(f"Upload realizado com sucesso! ID: {partes[1]}")
        else:
            print("Imagem enviada com sucesso!")


# list

def listar_imagens(sock):
    enviar_linha(sock, "LIST")

    resposta = receber_linha(sock)

    if not verificar_resposta(resposta):
        return

    partes = resposta.split("|")

    if len(partes) != 2:
        print("Resposta inválida do servidor.")
        return

    try:
        quantidade = int(partes[1])
    except ValueError:
        print("Quantidade de imagens inválida.")
        return

    print(f"\nImagens disponíveis: {quantidade}")

    if quantidade == 0:
        return

    print("-" * 95)
    print(f"{'ID':<14} {'NOME':<22} {'AUTOR':<15} {'DATA':<22} {'TAMANHO':>10}")
    print("-" * 95)

    for _ in range(quantidade):
        linha = receber_linha(sock)
        campos = linha.split("|")

        if len(campos) != 5:
            print("Registro inválido recebido.")
            continue

        id_img, nome, autor, data, tamanho = campos

        print(
            f"{id_img:<14} "
            f"{nome:<22} "
            f"{autor:<15} "
            f"{data:<22} "
            f"{tamanho:>10}"
        )

    print("-" * 95)


# download e view

def baixar_arquivo(sock, comando):
    identificador = input("Informe o ID ou nome da imagem: ").strip()

    if not identificador or "|" in identificador:
        print("Identificador inválido.")
        return

    enviar_linha(sock, f"{comando}|{identificador}")

    resposta = receber_linha(sock)

    if not verificar_resposta(resposta):
        return

    partes = resposta.split("|")

    if len(partes) != 3:
        print("Resposta inválida do servidor.")
        return

    try:
        tamanho = int(partes[1])
    except ValueError:
        print("Tamanho de arquivo inválido.")
        return

    nome = partes[2]

    if tamanho < 0 or tamanho > TAMANHO_MAXIMO:
        print("Tamanho de arquivo inválido.")
        return

    # recebe os bytes
    conteudo = receber_bytes(sock, tamanho)

    # cria a pasta de downloads, caso não exista
    PASTA_DOWNLOADS.mkdir(parents=True, exist_ok=True)

    # evita que o nome recebido pelo servidor crie caminhos errados
    nome = nome.replace("\\", "/").split("/")[-1]

    if not nome or nome in {".", ".."} or "|" in nome:
        print("Nome de arquivo recebido inválido.")
        return

    caminho = PASTA_DOWNLOADS / nome

    # salva o arquivo
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)

    print(f"\nArquivo salvo em: {caminho}")

    # VIEW abre a miniatura automaticamente
    if comando == "VIEW":
        try:
            if sys.platform == "win32":
                os.startfile(caminho)
            elif sys.platform == "darwin":
                os.system(f'open "{caminho}"')
            else:
                os.system(f'xdg-open "{caminho}"')

        except Exception:
            print("Não foi possível abrir a imagem automaticamente.")


def download(sock):
    baixar_arquivo(sock, "DOWNLOAD")


def visualizar(sock):
    baixar_arquivo(sock, "VIEW")


# historico

def mostrar_historico(sock):
    enviar_linha(sock, "HIST")

    resposta = receber_linha(sock)

    if not verificar_resposta(resposta):
        return

    partes = resposta.split("|")

    if len(partes) != 2:
        print("Resposta inválida do servidor.")
        return

    try:
        quantidade = int(partes[1])
    except ValueError:
        print("Quantidade inválida.")
        return

    print(f"\nÚltimas ações: {quantidade}")
    print("-" * 75)

    for _ in range(quantidade):
        linha = receber_linha(sock)
        campos = linha.split("|")

        if len(campos) != 4:
            print("Registro inválido.")
            continue

        data, usuario, acao, id_img = campos

        print(f"Data: {data}")
        print(f"Usuário: {usuario}")
        print(f"Ação: {acao}")
        print(f"Imagem: {id_img}")
        print("-" * 75)


# menu

def mostrar_menu():
    print("\n========== REPOSITÓRIO DE IMAGENS ==========")
    print("1 - Login")
    print("2 - Enviar imagem (UPLOAD)")
    print("3 - Listar imagens (LIST)")
    print("4 - Baixar imagem (DOWNLOAD)")
    print("5 - Visualizar miniatura (VIEW)")
    print("6 - Histórico (HIST)")
    print("0 - Sair")
    print("============================================")


def executar_cliente(host, porta):

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:

            print(f"Conectando ao servidor {host}:{porta}...")

            client.connect((host, porta))

            print("Conectado com sucesso!")

            while True:

                mostrar_menu()

                opcao = input("Escolha uma opção: ").strip()

                try:
                    if opcao == "1":
                        fazer_login(client)

                    elif opcao == "2":
                        upload(client)

                    elif opcao == "3":
                        listar_imagens(client)

                    elif opcao == "4":
                        download(client)

                    elif opcao == "5":
                        visualizar(client)

                    elif opcao == "6":
                        mostrar_historico(client)

                    elif opcao == "0":
                        enviar_linha(client, "SAIR")

                        resposta = receber_linha(client)

                        print(resposta)
                        break

                    else:
                        print("Opção inválida.")

                except (ConnectionError, OSError) as erro:
                    print(f"\nErro na comunicação: {erro}")
                    break

                except (ValueError, UnicodeDecodeError) as erro:
                    print(f"\nResposta inválida: {erro}")

    except ConnectionRefusedError:
        print("Não foi possível conectar. Verifique se o servidor está ligado.")

    except OSError as erro:
        print(f"Erro de conexão: {erro}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Cliente do Repositório Colaborativo de Imagens"
    )

    parser.add_argument(
        "host",
        nargs="?",
        default="127.0.0.1",
        help="IP do servidor (padrão: 127.0.0.1)"
    )

    parser.add_argument(
        "porta",
        nargs="?",
        type=int,
        default=5000,
        help="Porta do servidor (padrão: 5000)"
    )

    args = parser.parse_args()

    executar_cliente(args.host, args.porta)