import bpy, glob, re, subprocess, os, traceback
from collections import defaultdict
from pathlib import Path

bl_info = {
  'name': 'Substance Import-Export Tools',
  'version': (1, 3, 24),
  'author': 'passivestar',
  'blender': (4, 1, 0),
  'location': '3D View N Panel',
  'description': 'Simplifies Export to Substance Painter',
  'category': 'Import-Export'
}

# @Util

def detect_substance_painter_path():
  paths = []

  current_os = os.name

  if current_os == 'posix':
    # MacOS
    paths.extend([
        f'/Applications/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter',
        f'/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter',
        f'~/Library/Application Support/Steam/steamapps/common/Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter'
    ])
    # MacOS with year
    for year in range(2020, 2026):
      paths.extend([
          f'/Applications/Adobe Substance 3D Painter {year}.app/Contents/MacOS/Adobe Substance 3D Painter',
          f'/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter {year}.app/Contents/MacOS/Adobe Substance 3D Painter',
          f'~/Library/Application Support/Steam/steamapps/common/Substance 3D Painter {year}/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter'
      ])
  elif current_os == 'nt':
    # Windows
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
      paths.extend([
          # CC
          f'{letter}:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\Adobe Substance 3D Painter.exe',
          f'{letter}:\\Program Files (x86)\\Adobe\\Adobe Substance 3D Painter\\Adobe Substance 3D Painter.exe',

          # Steam without 3D
          f'{letter}:\\Program Files\\Steam\\steamapps\\common\\Substance Painter\\Adobe Substance 3D Painter.exe'
          f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance Painter\\Adobe Substance 3D Painter.exe'

          # Steam with 3D
          f'{letter}:\\Program Files\\Steam\\steamapps\\common\\Substance 3D Painter\\Adobe Substance 3D Painter.exe'
          f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance 3D Painter\\Adobe Substance 3D Painter.exe'
      ])
      # Windows with year
      for year in range(2020, 2026):
        paths.extend([
            # CC
            f'{letter}:\\Program Files\\Adobe\\Adobe Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe',
            f'{letter}:\\Program Files (x86)\\Adobe\\Adobe Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe',

            # Steam without 3D
            f'{letter}:\\Program Files\\Steam\\steamapps\\common\\Substance Painter {year}\\Adobe Substance 3D Painter.exe'
            f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance Painter {year}\\Adobe Substance 3D Painter.exe'

            # Steam with 3D
            f'{letter}:\\Program Files\\Steam\\steamapps\\common\\Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe'
            f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe'
        ])

  # Check each path for the current operating system and return the first one that exists
  for path in paths:
    path = os.path.expanduser(path)
    try:
      if Path(path).exists():
        return path
    except Exception as e:
      pass

  # If none of the paths exist, return an empty string
  return ''

def material_needs_setup(material):
  if material.node_tree is None:
    return False
  if len(material.node_tree.nodes) == 2:
    return True
  return False

# Mock data for testing through blender text editor without installing
mocks = {
  'painter_path': detect_substance_painter_path(),
  'textures_path': ''
}

def get_paths(context):
  textures_path = get_preferences(context)["textures_path"]

  if textures_path == '':
    textures_path = Path(bpy.path.abspath('//'))
  else:
    textures_path = Path(textures_path)
  
  collection_name_clean = re.sub(r'[^a-zA-Z0-9_]', '_', bpy.context.view_layer.active_layer_collection.name)

  textures_path_for_collection = textures_path.joinpath('textures_' + collection_name_clean + '/')

  fbx_path = textures_path_for_collection.joinpath(collection_name_clean + '.fbx')
  spp_path = textures_path_for_collection.joinpath(collection_name_clean + '.spp')

  return {
    'fbx': fbx_path,
    'spp': spp_path,
    'directory': textures_path_for_collection,
    'collection_name_clean': collection_name_clean
  }

def get_preferences(context):
  if __name__ == '__main__':
    return mocks
  else:
    prefs = context.preferences.addons[__name__].preferences
    return {
      'painter_path': prefs.painter_path,
      'textures_path': prefs.textures_path
    }

def object_has_material(obj):
  return len(obj.data.materials) > 0 and obj.data.materials[0] is not None

def create_material_for_object(obj):
  material = bpy.data.materials.new(name=obj.name)
  material.use_nodes = True
  material.node_tree.nodes.clear()
  principled_bsdf = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
  material_output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
  material.node_tree.links.new(principled_bsdf.outputs['BSDF'], material_output.inputs['Surface'])
  if len(obj.data.materials) > 0:
    obj.data.materials[0] = material
  else:
    obj.data.materials.append(material)

# @Operators

class ExportToSubstancePainterOperator(bpy.types.Operator):
  """Export Collection to Substance Painter. Press Ctrl+Shift+R in Painter to reload after re-export"""
  bl_idname, bl_label = 'st.open_in_substance_painter', 'Export Collection to Substance Painter'

  run_painter: bpy.props.BoolProperty(name='Run Substance Painter', default=True)

  def execute(self, context):
    preferences = get_preferences(context)
    painter_path = preferences["painter_path"]

    paths = get_paths(context)
    directory = paths['directory']
    fbx = paths['fbx']
    spp = paths['spp']

    if bpy.data.filepath == '':
      self.report({'ERROR'}, 'File is not saved. Please save your blend file')
      return {'FINISHED'}

    for o in bpy.context.view_layer.active_layer_collection.collection.objects:
      # Check if the object is mesh:
      if o.type != 'MESH':
        self.report({'ERROR'}, f'Object {o.name} is not a mesh')
        return {'FINISHED'}

      # Check if the object has a material and create if necessary:
      if not object_has_material(o):
        create_material_for_object(o)
    
    if not directory.exists():
      directory.mkdir(parents=True, exist_ok=True)

    # Export FBX
    bpy.ops.wm.save_mainfile()
    bpy.ops.export_scene.fbx(
      mesh_smooth_type='EDGE',
      use_mesh_modifiers=True,
      add_leaf_bones=False,
      apply_scale_options='FBX_SCALE_ALL',
      bake_anim_use_nla_strips=False,
      bake_space_transform=True,
      use_active_collection=True,
      filepath=str(fbx)
    )

    # If we only need to export the fbx, we're done
    if not self.run_painter:
      return {'FINISHED'}

    if painter_path == '':
      self.report({'ERROR'}, 'Please specify Substance Painter path in addon preferences')
      return {'FINISHED'}

    # Check if preferences.painter_path exists
    if not Path(painter_path).exists():
      self.report({'ERROR'}, 'Substance Painter path is not valid. Please set the corrent path to Substance Painter in addon preferences')
      return {'FINISHED'}

    # Check if a mac .app and add the executable part automatically first
    if os.name == 'posix' and painter_path.endswith('.app'):
      painter_path = painter_path + '/Contents/MacOS/Adobe Substance 3D Painter'
    
    # Display an error message if the path is a directory
    if os.path.isdir(painter_path):
      self.report({'ERROR'}, 'Substance Painter path is set to a directory. Please set it to the executable file')
      return {'FINISHED'}

    try:
      if os.name == 'nt':
        subprocess.Popen([painter_path, '--mesh', fbx, '--export-path', directory, spp])
      else:
        subprocess.Popen(f'"{painter_path}" --mesh "{fbx}" --export-path "{directory}" "{spp}"', shell=True)

    except Exception as e:
      self.report({'ERROR'}, f'Error opening Substance Painter: {e}')
      return {'FINISHED'}

    return {'FINISHED'}

class LoadSubstancePainterTexturesOperator(bpy.types.Operator):
  """Load Substance Painter Textures"""
  bl_idname, bl_label, bl_options = 'st.load_substance_painter_textures', 'Load Substance Painter Textures', {'REGISTER', 'UNDO'}

  def execute(self, context):
    preferences = get_preferences(context)

    paths = get_paths(context)
    directory = paths['directory']

    # Check that node wrangler is enabled
    if 'node_wrangler' not in bpy.context.preferences.addons:
      self.report({'ERROR'}, 'Node Wrangler needs to be enabled! Please enable it in Edit -> Preferences -> Add-ons')
      return {'FINISHED'}

    # All of the materials in the blend file
    material_names = [material.name for material in bpy.data.materials]

    # Reload all of the unique images in materials of the current collection
    unique_images = set()
    for obj in bpy.context.view_layer.active_layer_collection.collection.objects:
      if obj.type == 'MESH' and len(obj.data.materials) > 0:
        for material in obj.data.materials:
          if material is not None and material.use_nodes:
            for node in material.node_tree.nodes:
              if node.bl_idname == 'ShaderNodeTexImage':
                unique_images.add(node.image)
    for image in unique_images:
      image.reload()

    # Return if the file is not save
    if bpy.data.filepath == '':
      self.report({'ERROR'}, 'File is not saved')
      return {'FINISHED'}

    # Return if the texture folder doesn't exist
    if not directory.exists():
      self.report({'ERROR'}, 'There is no texture folder')
      return {'FINISHED'}

    # Return if there are no materials in the scene
    if len(bpy.data.materials) == 0:
      self.report({'ERROR'}, 'There are no materials in the scene')
      return {'FINISHED'}

    # Iterate through all of the files and group them by texture set name (material)
    texture_sets = defaultdict(list)
    material_names = sorted([material.name for material in bpy.data.materials if material_needs_setup(material)], key=len, reverse=True)
    for texture_file in directory.iterdir():
      # If texture_file is not a common texture file extension, skip it
      if texture_file.suffix not in ['.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff', '.bmp', '.exr']:
        continue
      for material_name in material_names:
        if material_name in texture_file.name:
          texture_sets[material_name].append(texture_file.name)
          break
    # Create an empty mesh object with an empty material slot and set it as active
    # This is needed to be able to use the shader editor to assign textures with node wrangler
    previous_active_object = context.view_layer.objects.active
    temp_mesh = bpy.data.meshes.new(name="TempMesh")
    temp_obj = bpy.data.objects.new(name="TempObject", object_data=temp_mesh)
    temp_obj.data.materials.append(None)
    context.scene.collection.objects.link(temp_obj)
    context.view_layer.objects.active = temp_obj

    # Set area type to node editor
    previous_context = context.area.type
    context.area.type = 'NODE_EDITOR'
    context.area.ui_type = 'ShaderNodeTree'

    # Try catch to make sure that the context is ALWAYS returned to the previous one
    # Otherwise the UI may break
    try:
      # For all of the texture sets that have a material with matching name add nodes via node wrangler
      for texture_set_name, texture_file_names in texture_sets.items():
        if texture_set_name in material_names:
          # Set node editor to current material
          material = bpy.data.materials[texture_set_name]
          context.object.data.materials[0] = material
          context.space_data.node_tree = material.node_tree
          # Select the Principled BSDF node
          for node in context.space_data.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
              context.space_data.node_tree.nodes.active = node
              break
          # Add textures to node tree using node wrangler
          directory = str(directory) + os.sep
          files = [{'name':n} for n in texture_file_names]
          bpy.ops.node.nw_add_textures_for_principled(directory=directory, files=files)
    except Exception as e:
      tb = traceback.format_exc()
      self.report({'ERROR'}, f'Error occurred while adding textures: {e}\n{tb}')
    finally:
      context.area.type = previous_context
      context.view_layer.objects.active = previous_active_object
      bpy.data.objects.remove(temp_obj)

    return {'FINISHED'}

# @UI

class SubstanceToolsPanel(bpy.types.Panel):
  """Substance Tools Panel"""
  bl_idname = 'SCENE_PT_substance_tools'
  bl_label = 'Substance Painter Tools'
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = 'Substance'

  def draw(self, context):
    layout = self.layout

    paths = get_paths(context)
    fbx = paths['fbx']
    collection_name_clean = paths['collection_name_clean']

    fbx_exists = Path(fbx).exists()

    box_column = layout.box().column(align=True)

    if collection_name_clean == 'Scene_Collection':
      box_column.label(text='Select a collection in the outliner')
    else:
      box_column.label(text=f'Collection: {collection_name_clean}')
      box_column.separator()
      column = box_column.column(align=True)
      column.operator('st.open_in_substance_painter', text=f'Export', icon='EXPORT').run_painter = False
      column.operator('st.open_in_substance_painter', text=f'Export and Open in Painter', icon='WINDOW').run_painter = True

      if fbx_exists:
        # Load textures button
        if 'node_wrangler' in bpy.context.preferences.addons:
          column.operator('st.load_substance_painter_textures', text='Load Painter Textures', icon='IMPORT')
        else:
          column.label(text='Node Wrangler addon needs to be enabled!')
          column.label(text='Please enable it in Edit -> Preferences -> Add-ons')

# @Preferences

class SubstanceToolsPreferences(bpy.types.AddonPreferences):
  bl_idname = __name__

  painter_path: bpy.props.StringProperty(name='Substance Painter Executable', default=detect_substance_painter_path(), subtype='FILE_PATH')
  textures_path: bpy.props.StringProperty(name='Export Path (Blank for blend file path)', default='', subtype='DIR_PATH')

  def draw(self, context):
    layout = self.layout
    layout.prop(self, 'painter_path')
    layout.prop(self, 'textures_path')

# @Register

classes = (
  ExportToSubstancePainterOperator,
  LoadSubstancePainterTexturesOperator,

  SubstanceToolsPanel,

  SubstanceToolsPreferences
)

def register():
  for c in classes: bpy.utils.register_class(c)

def unregister():
  for c in classes: bpy.utils.unregister_class(c)

if __name__ == '__main__': register()