import sympy
import FreeCAD
import Part
import os
from enum import Enum, auto


class Orientation(Enum):
    FACE = auto()    # você está de frente para o objeto
    LATERAL = auto()  # você está de frente para o objeto então o gira como uma porta
    TOPO = auto()    # você está de frente para o objeto então o tomba como um dominó


VARSET_NAME = "params"


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


def create_painel(doc, width, height, thickness, orientation: Orientation = Orientation.FACE, position=(0, 0, 0), name="Panel"):
    """
    Cria um objeto Painel (Box) no FreeCAD.

    :param width: Largura (float, string ou sympy).
    :param height: Altura (float, string ou sympy).
    :param thickness: Espessura (float, string ou sympy).
    :param orientation: Enum Orientation (FACE, LATERAL, TOPO).
    :param position: Tupla (x, y, z).
    :param name: Nome do objeto.
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
    if orientation == Orientation.FACE:
        pass
    elif orientation == Orientation.LATERAL:
        rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
    elif orientation == Orientation.TOPO:
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

    :param doc: Documento FreeCAD.
    :param kwargs: Variáveis a serem adicionadas (ex: Largura=100.0).
    """
    obj = doc.addObject("App::VarSet", VARSET_NAME)
    for key, value in kwargs.items():
        obj.addProperty("App::PropertyLength", key)
        setattr(obj, key, value)

    return obj


# --- Bloco de Teste ---
if __name__ == "__main__" or __name__ == "elements":
    # Criar documento
    doc_name = "TestePaineis"
    if FreeCAD.activeDocument() and FreeCAD.activeDocument().Name == doc_name:
        FreeCAD.closeDocument(doc_name)
    doc = FreeCAD.newDocument(doc_name)

    # Parâmetros comuns
    W = 100.0  # Largura
    H = 200.0  # Altura original (comprimento se deitado)
    T = 15.0  # Espessura

    # 0. Criar VarSet primeiro (para as fórmulas funcionarem)
    create_varset(doc, Largura=W, Altura=H, Espessura=T)

    # 1. Painel de Frente (Parede de Fundo) - Usando referências ao VarSet
    # Nota: Usamos f"{VARSET_NAME}.NomeProp"
    create_painel(doc,
                  width=f"{VARSET_NAME}.Largura",
                  height=f"{VARSET_NAME}.Altura",
                  thickness=f"{VARSET_NAME}.Espessura",
                  orientation=Orientation.FACE,
                  position=(0, 0, 0), name="PainelFrente_Parametrico")

    # 2. Painel Lateral (Parede Lateral) - Usando fórmula na posição
    # Position x = -Espessura
    create_painel(doc,
                  width=f"{VARSET_NAME}.Largura",
                  height=f"{VARSET_NAME}.Altura",
                  thickness=f"{VARSET_NAME}.Espessura",
                  orientation=Orientation.LATERAL,
                  position=(f"-{VARSET_NAME}.Espessura", 0, 0),
                  name="PainelLateral_Parametrico")

    # 3. Painel de Topo
    create_painel(doc,
                  width=f"{VARSET_NAME}.Largura",
                  height=f"{VARSET_NAME}.Altura",
                  thickness=f"{VARSET_NAME}.Espessura",
                  orientation=Orientation.TOPO,
                  position=(0, 0, f"{VARSET_NAME}.Altura"),
                  name="PainelTopo_Parametrico")

    # 4. Painel Flutuante (Todas as posições por fórmula)
    # Ex: x = Largura, y = Espessura, z = Altura/2
    create_painel(doc,
                  width=f"{VARSET_NAME}.Largura",
                  height="500",
                  thickness=T,
                  orientation=Orientation.FACE,
                  position=(f"{VARSET_NAME}.Largura",
                            f"{VARSET_NAME}.Espessura", f"{VARSET_NAME}.Altura / 2"),
                  name="PainelFlutuante_FullExpr")

    # Finalização
    doc.recompute()

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "paineis_parametricos.FCStd")
    doc.saveAs(filename)

    print(f"Arquivo gerado com sucesso: {filename}")
