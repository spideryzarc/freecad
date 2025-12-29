from elements import create_panel, create_varset, Orientation, VARSET_NAME, var
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


def create_plinth(doc, height, width, depth, thickness, position=(0, 0, 0),
                  offset_front=0, offset_back=0, offset_left=0, offset_right=0,
                  name="plinth"):
    """
    Cria um soco/rodapé (base recuada) parametrizado com recuos opcionais.

    Args:
        doc: Documento do FreeCAD.
        height: Altura do rodapé.
        width: Largura total disponível (antes dos recuos).
        depth: Profundidade total disponível (antes dos recuos).
        thickness: Espessura das placas.
        position: Tupla (x, y, z) com a posição inicial de referência.
        offset_front: Recuo frontal.
        offset_back: Recuo traseiro.
        offset_left: Recuo esquerdo.
        offset_right: Recuo direito.
        name: Nome base para os objetos criados.
    """
    # 1. Dimensões Efetivas
    eff_width = width - offset_left - offset_right
    eff_depth = depth - offset_front - offset_back

    # Validar dimensões positivas (opcional, mas bom ter em mente que pode dar erro se negativo)
    # No FreeCAD paramétrico com VarSets, apenas passamos as vars, o erro estouraria na geometria se fosse negativo.

    # 2. Dimensões Derivadas
    # Profundidade interna das laterais = Depth Efetivo - 2*Thickness
    inner_depth = eff_depth - 2 * thickness

    # 3. Posição Inicial Efetiva (considerando recuos Left e Front)
    # Base assume que Y cresce para "trás" (Depth) e X para "direita" (Width)
    ref_x, ref_y, ref_z = position
    start_x = ref_x + offset_left
    start_y = ref_y + offset_front
    z_pos = ref_z

    # 4. Criação dos Painéis

    # --- Frontal e Traseira (Dominantes) ---

    # Frontal (posicionado em start_y)
    create_panel(doc, name=f"{name}_front",
                 width=eff_width, height=height, thickness=thickness,
                 orientation=Orientation.FRONT,
                 position=(start_x, start_y, z_pos))

    # Traseira (recuada em Y: start_y + eff_depth - Thickness)
    create_panel(doc, name=f"{name}_back",
                 width=eff_width, height=height, thickness=thickness,
                 orientation=Orientation.FRONT,
                 position=(start_x, start_y + eff_depth - thickness, z_pos))

    # --- Laterais (Ensanduichadas) ---

    # Lateral Esquerda (X=start_x + Thickness, Y=start_y + Thickness)
    create_panel(doc, name=f"{name}_left",
                 width=inner_depth, height=height, thickness=thickness,
                 orientation=Orientation.SIDE,
                 position=(start_x + thickness, start_y + thickness, z_pos))

    # Lateral Direita (X=start_x + eff_width, Y=start_y + Thickness)
    # Na orientação SIDE +90Z, X é a face "traseira" local, então X=Right Edge
    create_panel(doc, name=f"{name}_right",
                 width=inner_depth, height=height, thickness=thickness,
                 orientation=Orientation.SIDE,
                 position=(start_x + eff_width, start_y + thickness, z_pos))


def create_niche(doc, height, width, depth, thickness, position=(0, 0, 0), name="niche", back_ratio: float = 0):
    """
    Cria um nicho parametrizado composto por 4 painéis e opcionalmente um fundo.

    Args:
        doc: Documento do FreeCAD.
        height: Altura total.
        width: Largura total.
        depth: Profundidade total.
        thickness: Espessura das placas.
        position: Tupla (x, y, z) com a posição inicial.
        name: Nome base para os objetos.
        back_ratio: Proporção do fundo (0 = sem fundo, 1 = fundo total, 0 < x < 1 = fundo bipartido).
    """
    # 1. Definição das Dimensões Derivadas
    # Altura interna = Height - 2*Thickness
    inner_height = height - 2 * thickness

    x_pos, y_pos, z_pos = position

    # 2. Criação dos Painéis

    # --- Laterais (Ensanduichadas Verticalmente) ---
    # Lateral Esquerda: X=Thickness, Z=Thickness
    create_panel(doc, name=f"{name}_left",
                 height=inner_height, width=depth, thickness=thickness,
                 orientation=Orientation.SIDE,
                 position=(x_pos + thickness, y_pos, z_pos + thickness))

    # Lateral Direita: X=Width, Z=Thickness
    create_panel(doc, name=f"{name}_right",
                 height=inner_height, width=depth, thickness=thickness,
                 orientation=Orientation.SIDE,
                 position=(x_pos + width, y_pos, z_pos + thickness))

    # --- Base e Topo (Dominantes Horizontalmente) ---
    # Base: Z=Thickness (Ocupa de Thickness até 0) - Orientação Topo -90X -> Espessura vai pra Z negativo.
    # Então se Z=Thickness, ocupa de Thickness à 0.
    create_panel(doc, name=f"{name}_base",
                 height=depth, width=width, thickness=thickness,
                 orientation=Orientation.TOP,
                 position=(x_pos, y_pos, z_pos + thickness))

    # Topo: Z=Height (Ocupa de Height à Height-Thickness)
    create_panel(doc, name=f"{name}_top",
                 height=depth, width=width, thickness=thickness,
                 orientation=Orientation.TOP,
                 position=(x_pos, y_pos, z_pos + height))

    # Fundo (Back Panel)
    if back_ratio > 0.001:
        if back_ratio >= .999:
            # Painel de altura inner_height fechando completamente o fundo
            create_panel(doc, name=f"{name}_back",
                         width=width - 2 * thickness,
                         height=inner_height,
                         thickness=thickness,
                         orientation=Orientation.FRONT,
                         position=(x_pos + thickness, y_pos + depth - thickness, z_pos + thickness))
        else:
            # Dois painéis de altura back_ratio*inner_height/2 fechando o fundo, em cima e em baixo
            strip_height = (back_ratio * inner_height) / 2

            # Painel Superior (Topo do fundo)
            create_panel(doc, name=f"{name}_back_top",
                         width=width - 2 * thickness,
                         height=strip_height,
                         thickness=thickness,
                         orientation=Orientation.FRONT,
                         position=(x_pos + thickness, y_pos + depth - thickness, z_pos + height - thickness - strip_height))

            # Painel Inferior (Base do fundo)
            create_panel(doc, name=f"{name}_back_bottom",
                         width=width - 2 * thickness,
                         height=strip_height,
                         thickness=thickness,
                         orientation=Orientation.FRONT,
                         position=(x_pos + thickness, y_pos + depth - thickness, z_pos + thickness))


def create_wardrobe_composition(doc):
    """
    Cria uma composição de teste: Nicho sobre Rodapé.
    """
    # 1. Definir VarSet Único
    create_varset(doc,
                  Width=800.0,
                  Depth=300.0,
                  Thickness=15.0,
                  Plinth_Height=150.0,
                  Niche_Height=500.0,
                  Plinth_Offset_Front=20.0,
                  Plinth_Offset_Back=20.0,
                  Plinth_Offset_Left=20.0,
                  Plinth_Offset_Right=20.0)

    # 2. Obter símbolos
    W = var("Width")
    D = var("Depth")
    T = var("Thickness")
    H_P = var("Plinth_Height")
    H_N = var("Niche_Height")

    Off_F = var("Plinth_Offset_Front")
    Off_B = var("Plinth_Offset_Back")
    Off_L = var("Plinth_Offset_Left")
    Off_R = var("Plinth_Offset_Right")

    # 3. Criar Rodapé na base (0,0,0)
    create_plinth(doc, height=H_P, width=W, depth=D,
                  thickness=T, position=(0, 0, 0),
                  offset_front=Off_F, offset_back=Off_B,
                  offset_left=Off_L, offset_right=Off_R)

    # 4. Criar Nicho em cima do Rodapé (0,0, H_P)
    # Com fundo total (ratio=1)
    create_niche(doc, height=H_N, width=W, depth=D, thickness=T,
                 position=(0, 0, H_P), back_ratio=1)


# --- Bloco de Teste ---
if __name__ in ["__main__", "compositions"]:
    print("Iniciando composição de Nicho...")

    doc_name = "TestNiche"
    # Fechar documento existente se houver para evitar duplicidade
    if FreeCAD.activeDocument() and FreeCAD.activeDocument().Name == doc_name:
        FreeCAD.closeDocument(doc_name)

    doc = FreeCAD.newDocument(doc_name)

    # Parâmetros de teste
    # --- Teste Composição ---
    print("Testando Composição (Niche + Plinth)...")
    create_wardrobe_composition(doc)

    doc.recompute()

    # Salvar e reportar
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "wardrobe_composition.FCStd")
    doc.saveAs(filename)

    print(f"Gerado com sucesso: {filename}")
