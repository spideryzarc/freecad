import sympy
import FreeCAD
import Part
import os
from enum import Enum, auto


class Orientation(Enum):
    # Vertical | Plano XZ | Ex: Fundos, Portas, Painéis Frontais.
    FRONT = auto()
    # Vertical | Plano YZ | Ex: Laterais de móveis, Divisórias.
    SIDE = auto()
    # Horizontal | Plano XY | Ex: Prateleiras, Base, Topo, Tampos.
    TOP = auto()


VARSET_NAME = "params"


def header_var(name):
    """Retorna um símbolo do sympy referenciando uma propriedade do VarSet (wrapper legado para 'var')."""
    return sympy.Symbol(f"{VARSET_NAME}.{name}")

# Mantendo alias 'var' se o usuário gostar, mas pelo plano mudamos nomes.
# O plano dizia: "Renomear função var para get_var (opcional... Decidi manter var)".
# Então vou manter `var`.


def var(name):
    """Retorna um símbolo do sympy referenciando uma propriedade do VarSet."""
    return sympy.Symbol(f"{VARSET_NAME}.{name}")


def _set_prop_or_expr(obj, prop_name, value):
    """Auxiliar para definir valor ou expressão em uma propriedade."""
    # Se for string ou sympy object, converte para string e define como expressão
    if isinstance(value, (str, sympy.Basic)):
        obj.setExpression(prop_name, str(value))
    else:
        # Tenta definir diretamente checkando se é float/int
        try:
            setattr(obj, prop_name, value)
        except Exception:
            # Fallback para string se for outro tipo
            obj.setExpression(prop_name, str(value))


def create_panel(doc, width, height, thickness, orientation: Orientation = Orientation.FRONT, position=(0, 0, 0), name="Panel"):
    """
    Cria um objeto Painel (Box) no FreeCAD.

    Args:
        doc: Documento FreeCAD.
        width: Largura (float, string ou sympy).
        height: Altura (float, string ou sympy).
        thickness: Espessura (float, string ou sympy).
        orientation: Enum Orientation (FRONT, SIDE, TOP).
        position: Tupla (x, y, z).
        name: Nome do objeto.
    """
    obj = doc.addObject("Part::Box", name)

    # Definir dimensões (Length, Width, Height)
    _set_prop_or_expr(obj, "Length", width)
    _set_prop_or_expr(obj, "Width", thickness)
    _set_prop_or_expr(obj, "Height", height)

    # Tratamento da Posição (Placement)
    # Separamos X, Y, Z. Se for numérico puro, vai pro Vector. Se for expr, setExpression.

    x_in, y_in, z_in = position

    # Defaults numéricos para o Placement base
    x_val, y_val, z_val = 0.0, 0.0, 0.0

    # Flags para saber se definimos expressão
    x_expr, y_expr, z_expr = None, None, None

    # Função auxiliar local para resolver valor/expressão
    def resolve(val):
        if isinstance(val, (str, sympy.Basic)):
            return 0.0, str(val)  # valor numérico dummy, expressão real
        return float(val), None

    x_val, x_expr = resolve(x_in)
    y_val, y_expr = resolve(y_in)
    z_val, z_expr = resolve(z_in)

    base_vector = FreeCAD.Vector(x_val, y_val, z_val)
    rotation = FreeCAD.Rotation()  # Rotação identidade

    # Aplicar Rotação baseada na Orientação
    if orientation == Orientation.FRONT:
        pass
    elif orientation == Orientation.SIDE:
        rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
    elif orientation == Orientation.TOP:
        rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)

    # Definir Placement base (valores numéricos)
    obj.Placement = FreeCAD.Placement(base_vector, rotation)

    # Aplicar expressões de posição se houver
    if x_expr:
        obj.setExpression("Placement.Base.x", x_expr)
    if y_expr:
        obj.setExpression("Placement.Base.y", y_expr)
    if z_expr:
        obj.setExpression("Placement.Base.z", z_expr)

    return obj


def create_varset(doc, **kwargs):
    """
    Cria o objeto VarSet padrão ('Parametros') no documento.

    Args:
        doc: Documento FreeCAD.
        kwargs: Variáveis a serem adicionadas (ex: Width=100.0).
    """
    obj = doc.addObject("App::VarSet", VARSET_NAME)
    for key, value in kwargs.items():
        obj.addProperty("App::PropertyLength", key)
        setattr(obj, key, value)

    return obj


# --- Bloco de Teste ---
if __name__ == "__main__" or __name__ == "elements":
    # Criar documento
    doc_name = "TestPanels"
    if FreeCAD.activeDocument() and FreeCAD.activeDocument().Name == doc_name:
        FreeCAD.closeDocument(doc_name)
    doc = FreeCAD.newDocument(doc_name)

    # Parâmetros comuns
    W = 100.0  # Largura
    H = 200.0  # Altura original (comprimento se deitado)
    T = 15.0  # Espessura

    # 0. Criar VarSet primeiro (para as fórmulas funcionarem)
    create_varset(doc, Width=W, Height=H, Thickness=T)

    # 1. Painel de Frente (Parede de Fundo) - Usando referências ao VarSet
    # Nota: Usamos f"{VARSET_NAME}.NomeProp"
    create_panel(doc,
                 width=f"{VARSET_NAME}.Width",
                 height=f"{VARSET_NAME}.Height",
                 thickness=f"{VARSET_NAME}.Thickness",
                 orientation=Orientation.FRONT,
                 position=(0, 0, 0), name="PanelFront_Parametric")

    # 2. Painel Lateral (Parede Lateral) - Usando fórmula na posição
    # Position x = -Espessura
    create_panel(doc,
                 width=f"{VARSET_NAME}.Width",
                 height=f"{VARSET_NAME}.Height",
                 thickness=f"{VARSET_NAME}.Thickness",
                 orientation=Orientation.SIDE,
                 position=(f"-{VARSET_NAME}.Thickness", 0, 0),
                 name="PanelSide_Parametric")

    # 3. Painel de Topo
    create_panel(doc,
                 width=f"{VARSET_NAME}.Width",
                 height=f"{VARSET_NAME}.Height",
                 thickness=f"{VARSET_NAME}.Thickness",
                 orientation=Orientation.TOP,
                 position=(0, 0, f"{VARSET_NAME}.Height"),
                 name="PanelTop_Parametric")

    # 4. Painel Flutuante (Todas as posições por fórmula)
    # Ex: x = Largura, y = Espessura, z = Altura/2
    create_panel(doc,
                 width=f"{VARSET_NAME}.Width",
                 height="500",
                 thickness=T,
                 orientation=Orientation.FRONT,
                 position=(f"{VARSET_NAME}.Width",
                           f"{VARSET_NAME}.Thickness", f"{VARSET_NAME}.Height / 2"),
                 name="PanelFloating_FullExpr")

    # Finalização
    doc.recompute()

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "parametric_panels.FCStd")
    doc.saveAs(filename)

    print(f"Arquivo gerado com sucesso: {filename}")
