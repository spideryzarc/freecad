import os
import FreeCAD
import Part

# Criar um novo documento
doc = FreeCAD.newDocument("TesteCubo")

# Adicionar um objeto Cubo (Box)
box = doc.addObject("Part::Box", "MeuCubo")

# Definir dimensões
box.Length = 10.0
box.Width = 10.0
box.Height = 10.0

# Recomputar o documento para atualizar a geometria
doc.recompute()

# Caminho para salvar o arquivo
filename = "output/teste_cubo.FCStd"
os.makedirs(os.path.dirname(filename), exist_ok=True)
doc.saveAs(filename)

print(f"Cubo criado e salvo em: {filename}")
