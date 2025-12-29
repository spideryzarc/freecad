from elements import create_painel, create_varset, Orientation, VARSET_NAME, var
import sympy
import FreeCAD
import Part
import os
import sys

# Garantir que o diretório atual está no path para importar elements
if "__file__" in globals():
    sys.path.append(os.path.dirname(__file__))
else:
    sys.path.append(os.getcwd())


def create_socalo(doc, h, w, d, t, pos=(0, 0, 0), name="socalo"):
    """
    Cria um soco/rodapé (base recuada) parametrizado.
    """
    # 1. Dimensões Derivadas
    # Profundidade interna das laterais = D - 2*T
    d_inner = d - 2 * t

    # 2. Criação dos Painéis
    x0, y0, z0 = pos

    # --- Frontal e Traseira (Dominantes) ---

    # Frontal (na origem Y=0 relativo)
    create_painel(doc, name=f"{name}_frente",
                  width=w, height=h, thickness=t,
                  orientation=Orientation.FACE,
                  position=(x0, y0, z0))

    # Traseira (recuada em Y: D-T)
    create_painel(doc, name=f"{name}_tras",
                  width=w, height=h, thickness=t,
                  orientation=Orientation.FACE,
                  position=(x0, y0 + d - t, z0))

    # --- Laterais (Ensanduichadas) ---

    # Lateral Esquerda (X=T, Y=T)
    create_painel(doc, name=f"{name}_esq",
                  width=d_inner, height=h, thickness=t,
                  orientation=Orientation.LATERAL,
                  position=(x0 + t, y0 + t, z0))

    # Lateral Direita (X=W, Y=T)
    # Nota: Na orientação Lateral +90Z, a posição é a face 'traseira' do painel em relação ao eixo X local
    # então se posicionamos em X=W, a espessura vai para X negativo (W-T até W), está correto.
    create_painel(doc, name=f"{name}_dir",
                  width=d_inner, height=h, thickness=t,
                  orientation=Orientation.LATERAL,
                  position=(x0 + w, y0 + t, z0))


def create_nincho(doc, h, w, d, t, pos=(0, 0, 0), name="nincho"):
    """
    Cria um nicho parametrizado composto por 4 painéis.
    """
    # 1. Definição das Dimensões Derivadas
    # Altura interna = H - 2*T
    h_inner = h - 2 * t

    x0, y0, z0 = pos

    # 2. Criação dos Painéis

    # --- Laterais (Ensanduichadas Verticalmente) ---
    # Lateral Esquerda: X=T, Z=T
    create_painel(doc, name=f"{name}_esq",
                  height=h_inner, width=d, thickness=t,
                  orientation=Orientation.LATERAL,
                  position=(x0 + t, y0, z0 + t))

    # Lateral Direita: X=W, Z=T
    create_painel(doc, name="PainelLateral2",
                  height=h_inner, width=d, thickness=t,
                  orientation=Orientation.LATERAL,
                  position=(x0 + w, y0, z0 + t))

    # --- Base e Topo (Dominantes Horizontalmente) ---
    # Base: Z=T (Ocupa de T até 0) - Orientação Topo -90X -> Espessura vai pra Z negativo.
    # Então se Z=T, ocupa de T à 0.
    create_painel(doc, name="PainelBase",
                  height=d, width=w, thickness=t,
                  orientation=Orientation.TOPO,
                  position=(x0, y0, z0 + t))

    # Topo: Z=H (Ocupa de H à H-T)
    create_painel(doc, name="PainelTopo",
                  height=d, width=w, thickness=t,
                  orientation=Orientation.TOPO,
                  position=(x0, y0, z0 + h))


def create_composta_armario(doc):
    """
    Cria uma composição de teste: Nicho sobre Socalo.
    """
    # 1. Definir VarSet Único
    create_varset(doc,
                  Largura=800.0,
                  Profundidade=300.0,
                  Espessura=15.0,
                  Altura_Socalo=150.0,
                  Altura_Nicho=500.0)

    # 2. Obter símbolos
    W = var("Largura")
    D = var("Profundidade")
    T = var("Espessura")
    H_S = var("Altura_Socalo")
    H_N = var("Altura_Nicho")

    # 3. Criar Socalo na base (0,0,0)
    create_socalo(doc, h=H_S, w=W, d=D, t=T, pos=(0, 0, 0))

    # 4. Criar Nicho em cima do Socalo (0,0, H_S)
    create_nincho(doc, h=H_N, w=W, d=D, t=T, pos=(0, 0, H_S))


# --- Bloco de Teste ---
if __name__ in ["__main__", "compositions"]:
    print("Iniciando composição de Nicho...")

    doc_name = "TesteNincho"
    # Fechar documento existente se houver para evitar duplicidade
    if FreeCAD.activeDocument() and FreeCAD.activeDocument().Name == doc_name:
        FreeCAD.closeDocument(doc_name)

    doc = FreeCAD.newDocument(doc_name)

    # Parâmetros de teste
    # --- Teste Composição ---
    print("Testando Composição (Nicho + Socalo)...")
    create_composta_armario(doc)

    doc.recompute()

    # Salvar e reportar
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "armario_composto.FCStd")
    doc.saveAs(filename)

    print(f"Gerado com sucesso: {filename}")
