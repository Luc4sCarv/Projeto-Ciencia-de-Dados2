import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Importa conexão e models do projeto
from database import SessionLocal
import models

BASE_DIR = Path(__file__).parent.resolve()

# ══════════════════════════════════════════════════════════════
#  PARÂMETROS DA BUSCA — altere aqui conforme necessário
# ══════════════════════════════════════════════════════════════
TIPO_OPERACAO = "ALUGUEL"      # ALUGUEL ou VENDA
TIPO_IMOVEL   = "APARTAMENTO"  # APARTAMENTO ou CASA
ESTADO        = "DF"
CIDADE        = "PLANO PILOTO"
BAIRRO        = "ASA NORTE"    # ou "ASA SUL", "TODOS", etc.

URL = "https://www.dfimoveis.com.br/"


# ══════════════════════════════════════════════════════════════
#  FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════

def extrair_numero(texto: str) -> float | None:
    """Extrai o primeiro número float de uma string."""
    if not texto:
        return None
    nums = re.findall(r"[\d.,]+", texto.replace(".", "").replace(",", "."))
    for n in nums:
        try:
            return float(n)
        except ValueError:
            continue
    return None


def garantir_tipo_operacao(db, nome: str) -> models.TipoOperacao:
    obj = db.query(models.TipoOperacao).filter_by(nome_operacao=nome.upper()).first()
    if not obj:
        obj = models.TipoOperacao(nome_operacao=nome.upper())
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def garantir_tipo_imovel(db, nome: str) -> models.TipoImovel:
    obj = db.query(models.TipoImovel).filter_by(nome_tipo_imovel=nome.upper()).first()
    if not obj:
        obj = models.TipoImovel(nome_tipo_imovel=nome.upper())
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def garantir_imobiliaria(db, nome: str) -> models.Imobiliaria:
    if not nome:
        nome = "Não informada"
    obj = db.query(models.Imobiliaria).filter_by(nome_imobiliaria=nome).first()
    if not obj:
        obj = models.Imobiliaria(nome_imobiliaria=nome)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def salvar_imovel(db, dado: dict, tipo_op_id: int, tipo_im_id: int, imob_id: int):
    """Salva um imóvel no banco, evitando duplicatas pelo endereço."""
    endereco = dado.get("endereco") or "Endereço não informado"

    # Evita duplicata pelo endereço + tipo operação
    existente = db.query(models.Imovel).filter_by(
        endereco=endereco,
        tipo_operacao_id=tipo_op_id
    ).first()
    if existente:
        print(f"  ↩ Já existe: {endereco[:60]}")
        return False

    imovel = models.Imovel(
        endereco=endereco,
        tamanho_m2=dado.get("tamanho_m2"),
        preco=dado.get("preco") or 0.0,
        quartos=dado.get("quartos"),
        vagas=dado.get("vagas"),
        suites=dado.get("suites"),
        imobiliaria_id=imob_id,
        tipo_operacao_id=tipo_op_id,
        tipo_imovel_id=tipo_im_id,
    )
    db.add(imovel)
    db.commit()
    print(f"  ✔ Salvo: {endereco[:60]} | R$ {dado.get('preco')}")
    return True


# ══════════════════════════════════════════════════════════════
#  SCRAPPER PRINCIPAL
# ══════════════════════════════════════════════════════════════

def rodar_scrapper():
    db = SessionLocal()

    # Garante que tipos existem no banco
    tipo_op  = garantir_tipo_operacao(db, TIPO_OPERACAO)
    tipo_im  = garantir_tipo_imovel(db, TIPO_IMOVEL)
    imob_gen = garantir_imobiliaria(db, "DFImóveis")

    # Configura o Chrome padrão
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-infobars")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Remove flag webdriver do navigator para evitar detecção
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    wait = WebDriverWait(driver, 20)

    total_salvos = 0
    total_vistos = 0

    try:
        driver.get(URL)

        # Limpa cookies/storage
        try:
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            driver.get(URL)
            time.sleep(2)
        except:
            pass

        # Aceita cookies se aparecer
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "btn-lgpd"))
            )
            btn.click()
            time.sleep(1)
        except:
            pass

        # Preenche os filtros do formulário
        filtros = [
            ("select2-negocios-container", TIPO_OPERACAO),
            ("select2-tipos-container",    TIPO_IMOVEL),
            ("select2-estados-container",  ESTADO),
            ("select2-cidades-container",  CIDADE),
            ("select2-bairros-container",  BAIRRO),
        ]

        for campo_id, valor in filtros:
            for tentativa in range(3):
                try:
                    campo = wait.until(EC.presence_of_element_located((By.ID, campo_id)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                    time.sleep(0.5)
                    try:
                        campo.click()
                    except:
                        driver.execute_script("arguments[0].click();", campo)

                    busca = wait.until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "select2-search__field"))
                    )
                    busca.send_keys(Keys.CONTROL, "a")
                    busca.send_keys(Keys.BACKSPACE)
                    busca.send_keys(valor)
                    time.sleep(1)

                    opcoes = driver.find_elements(
                        By.XPATH,
                        f"//li[contains(@class,'select2-results__option') and normalize-space()='{valor}']",
                    )
                    if opcoes:
                        try:
                            opcoes[0].click()
                        except:
                            driver.execute_script("arguments[0].click();", opcoes[0])
                    else:
                        busca.send_keys(Keys.ENTER)
                    break
                except Exception as e:
                    if tentativa == 2:
                        print(f"  ⚠ Falha no filtro '{campo_id}': {e}")
                    time.sleep(1)

            # Aguarda carregamento dos combos dependentes
            if campo_id in ("select2-estados-container", "select2-cidades-container"):
                time.sleep(3)
            else:
                time.sleep(1.5)

        # Clica em Pesquisar
        botao = wait.until(EC.element_to_be_clickable((By.ID, "botaoDeBusca")))
        botao.click()
        time.sleep(3)

        # ── Coleta página por página ──────────────────────────
        pagina = 1
        while True:
            print(f"\n📄 Página {pagina}...")

            wait.until(EC.presence_of_element_located((By.ID, "resultadoDaBuscaDeImoveis")))
            time.sleep(2)

            cards = driver.find_elements(
                By.XPATH,
                "//div[@id='resultadoDaBuscaDeImoveis']//a[contains(@href, '/imovel/')]",
            )
            print(f"   {len(cards)} cards encontrados")

            for card in cards:
                total_vistos += 1
                dado = {}

                # Endereço / título
                try:
                    dado["endereco"] = card.find_element(By.CLASS_NAME, "ellipse-text").text.strip()
                except:
                    dado["endereco"] = f"{CIDADE} - {BAIRRO}, DF"

                # Preço
                try:
                    preco_txt = card.find_element(By.CLASS_NAME, "body-large").text.strip()
                    dado["preco"] = extrair_numero(preco_txt)
                except:
                    dado["preco"] = None

                # Quartos
                try:
                    qt = card.find_element(
                        By.XPATH,
                        ".//div[contains(text(),'Quarto') and contains(@class,'rounded-pill')]"
                    ).text
                    dado["quartos"] = int(extrair_numero(qt) or 0) or None
                except:
                    dado["quartos"] = None

                # Metragem
                try:
                    m2 = card.find_element(
                        By.XPATH,
                        ".//div[contains(@class,'web-view') and contains(text(),'m²')]"
                    ).text
                    dado["tamanho_m2"] = extrair_numero(m2)
                except:
                    dado["tamanho_m2"] = None

                # Vagas
                try:
                    vg = card.find_element(
                        By.XPATH,
                        ".//div[contains(@class,'rounded-pill') and (contains(text(),'Vaga') or contains(text(),'Vagas'))]"
                    ).text
                    dado["vagas"] = int(extrair_numero(vg) or 0) or None
                except:
                    dado["vagas"] = None

                dado["suites"] = None  # site não expõe suítes nos cards

                # Salva no banco
                ok = salvar_imovel(db, dado, tipo_op.id, tipo_im.id, imob_gen.id)
                if ok:
                    total_salvos += 1

            # Próxima página
            try:
                proximo = driver.find_element(By.CSS_SELECTOR, "span.btn.next")
                if "disabled" in proximo.get_attribute("class"):
                    print("\n✅ Última página atingida.")
                    break
                driver.execute_script("arguments[0].click();", proximo)
                pagina += 1
                time.sleep(2)
            except:
                print("\n✅ Sem botão de próxima página — fim.")
                break

    finally:
        driver.quit()
        db.close()
        print(f"\n{'='*50}")
        print(f"Total visto:  {total_vistos} imóveis")
        print(f"Total salvo:  {total_salvos} imóveis novos no banco")
        print(f"{'='*50}")


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    rodar_scrapper()
