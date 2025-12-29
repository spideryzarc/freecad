from elements import create_painel, create_varset, Orientation, VARSET_NAME
import FreeCAD
import Part
import os
import sys

# Garantir que o diretório atual está no path para importar elements
if "__file__" in globals():
    sys.path.append(os.path.dirname(__file__))
else:
    sys.path.append(os.getcwd())


def create_socalo(doc, h, w, d, t):
    """
    Cria um soco/rodapé (base recuada) parametrizado.
    Semelhante a um nicho rotacionado (aberto em cima e em baixo).

    Topologia (Sanduíche Horizontal):
    - Frontal e Traseira são dominantes (Largura Total W).
    - Laterais são ensanduichadas entre a Frontal e Traseira (Profundidade reduzida).

    Diagrama Esquemático (Planif. Topo):
      ________________________  <-- PainelTras (Y = D-T)
     |                        |
     |   ||              ||   |
     |   ||              ||   | <-- PainelLateral (Entre Frente e Tras)
     |___||______________||___|
      ________________________  <-- PainelFrente (Y = 0)

    :param doc: Documento FreeCAD.
    :param h: Altura do soco.
    :param w: Largura total.
    :param d: Profundidade total.
    :param t: Espessura dos painéis.
    """
    # 1. Configuração de Variáveis Paramétricas
    create_varset(doc, Altura=h, Largura=w, Profundidade=d, Espessura=t)

    H = f"{VARSET_NAME}.Altura"
    W = f"{VARSET_NAME}.Largura"
    D = f"{VARSET_NAME}.Profundidade"
    T = f"{VARSET_NAME}.Espessura"

    # 2. Dimensões Derivadas
    # Profundidade interna das laterais = Profundidade - EspessuraFrente - EspessuraTras
    d_inner = f"{D} - 2 * {T}"

    # 3. Criação dos Painéis

    # --- Frontal e Traseira ---
    # Orientação FACE: Mantém X=Width, Y=Thickness, Z=Height.

    # Frontal (na origem Y=0)
    create_painel(doc, name="SocoFrente",
                  width=W, height=H, thickness=T,
                  orientation=Orientation.FACE,
                  position=(0, 0, 0))

    # Traseira (recuada em Y)
    create_painel(doc, name="SocoTras",
                  width=W, height=H, thickness=T,
                  orientation=Orientation.FACE,
                  position=(0, f"{D} - {T}", 0))

    # --- Laterais ---
    # Orientação LATERAL: Rotação +90 Z.
    # Dimensões nominais: height=Altura, width=ProfundidadeInner.
    # Rotação: Length(width) vai para Y, Thickness vai para -X.

    # Lateral Esquerda
    # Posição X=T (para ocupar de T até 0 no eixo X)
    # Posição Y=T (para começar após a frente)
    create_painel(doc, name="SocoEsq",
                  width=d_inner, height=H, thickness=T,
                  orientation=Orientation.LATERAL,
                  position=(T, T, 0))

    # Lateral Direita
    # Posição X=W (para ocupar de W até W-T no eixo X)
    create_painel(doc, name="SocoDir",
                  width=d_inner, height=H, thickness=T,
                  orientation=Orientation.LATERAL,
                  position=(W, T, 0))


def create_nincho(doc, h, w, d, t):
    """
    Cria um nicho parametrizado composto por 4 painéis (Base, Topo e duas Laterais).

    Topologia:
    - Base e Topo são dominantes (largura total W).
    - Laterais são ensanduichadas verticalmente entre a Base e o Topo.

    Diagrama Esquemático (Vista Frontal):
      ________________________  <-- PainelTopo (Z = H)
     |                        |
     |   ||              ||   |
     |   ||              ||   | <-- PainelLateral (Entre Base e Topo)
     |   ||              ||   |
     |___||______________||___|
      ________________________  <-- PainelBase (Z = 0)

    :param doc: Documento FreeCAD onde o nicho será criado.
    :param h: Altura total externa do nicho.
    :param w: Largura total externa do nicho.
    :param d: Profundidade total do nicho.
    :param t: Espessura do material dos painéis.
    """
    # 1. Configuração de Variáveis Paramétricas (VarSet)
    create_varset(doc, Altura=h, Largura=w, Profundidade=d, Espessura=t)

    # Aliases para referenciar as propriedades do VarSet nas fórmulas
    # Strings são usadas para manter a parametricidade no FreeCAD
    H = f"{VARSET_NAME}.Altura"
    W = f"{VARSET_NAME}.Largura"
    D = f"{VARSET_NAME}.Profundidade"
    T = f"{VARSET_NAME}.Espessura"

    # 2. Definição das Dimensões Derivadas
    # Altura interna das laterais = Altura Total - Base - Topo
    h_inner = f"{H} - 2 * {T}"

    # 3. Criação dos Painéis

    # --- Laterais ---
    # Orientação LATERAL: Painel vertical rotacionado em torno de Z.
    # Dimensões nominais: height=Altura Interna, width=Profundidade, thickness=Espessura.
    # Comportamento da Rotação (+90° Z): A espessura se estende no eixo X negativo a partir da origem.
    # Ajuste de Posição:
    # - Lateral Esquerda: X=T (para ocupar de 0 a T), Z=T (acima da base).
    # - Lateral Direita:  X=W (para ocupar de W-T a W), Z=T.

    create_painel(doc, name="PainelLateral1",
                  height=h_inner, width=D, thickness=T,
                  orientation=Orientation.LATERAL,
                  position=(T, 0, T))

    create_painel(doc, name="PainelLateral2",
                  height=h_inner, width=D, thickness=T,
                  orientation=Orientation.LATERAL,
                  position=(f"{W}", 0, T))

    # --- Base e Topo ---
    # Orientação TOPO: Painel horizontal rotacionado em torno de X.
    # Dimensões nominais: height=Profundidade, width=Largura Total, thickness=Espessura.
    # Comportamento da Rotação (-90° X): A espessura se estende no eixo Z negativo a partir da origem.
    # Ajuste de Posição:
    # - Base: Z=T (para ocupar de T até 0).
    # - Topo: Z=H (para ocupar de H até H-T).

    create_painel(doc, name="PainelBase",
                  height=D, width=W, thickness=T,
                  orientation=Orientation.TOPO,
                  position=(0, 0, T))

    create_painel(doc, name="PainelTopo",
                  height=D, width=W, thickness=T,
                  orientation=Orientation.TOPO,
                  position=(0, 0, f"{H}"))


# --- Bloco de Teste ---
if __name__ in ["__main__", "compositions"]:
    print("Iniciando composição de Nicho...")

    doc_name = "TesteNincho"
    # Fechar documento existente se houver para evitar duplicidade
    if FreeCAD.activeDocument() and FreeCAD.activeDocument().Name == doc_name:
        FreeCAD.closeDocument(doc_name)

    doc = FreeCAD.newDocument(doc_name)

    # Parâmetros de teste
    HEIGHT = 500.0
    WIDTH = 800.0
    DEPTH = 300.0
    THICKNESS = 15.0

    # --- Teste Soco ---
    print("Testando Soco...")
    SOCO_HEIGHT = 150.0
    create_socalo(doc, h=SOCO_HEIGHT, w=WIDTH, d=DEPTH, t=THICKNESS)

    doc.recompute()

    # Salvar e reportar
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "socolo_parametrico.FCStd")
    doc.saveAs(filename)

    print(f"Gerado com sucesso: {filename}")
