import bpy, glob, re, subprocess, os
from collections import defaultdict
from pathlib import Path

bl_info = {
  'name': 'Substance Import-Export Tools',
  'version': (1, 3, 3),
  'author': 'passivestar',
  'blender': (4, 0, 0),
  'location': '3D View N Panel',
  'description': 'Simplifies Export to Substance Painter',
  'category': 'Import-Export'
}

# @Util

def get_paths():
  directory = bpy.path.abspath('//')
  file = bpy.context.view_layer.active_layer_collection.name

  # Make sure that the file name is valid
  file = re.sub(r'[^a-zA-Z0-9_]', '_', file)

  return ( directory, file )

def detect_substance_painter_path():
  paths = []

  current_os = os.name

  if current_os == 'posix':
    paths.extend([
        f'/Applications/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter',  # macOS
        f'~/Library/Application Support/Steam/steamapps/common/Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter'  # macOS Steam
    ])
    for year in range(2020, 2026):
      paths.extend([
          f'/Applications/Adobe Substance 3D Painter {year}.app/Contents/MacOS/Adobe Substance 3D Painter',  # macOS
          f'~/Library/Application Support/Steam/steamapps/common/Substance 3D Painter {year}/Adobe Substance 3D Painter.app/Contents/MacOS/Adobe Substance 3D Painter'  # macOS Steam
      ])
  elif current_os == 'nt':
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
      paths.extend([
          f'{letter}:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\Adobe Substance 3D Painter.exe',  # Windows
          f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance 3D Painter\\Adobe Substance 3D Painter.exe'  # Windows Steam
      ])
      for year in range(2020, 2026):
        paths.extend([
            f'{letter}:\\Program Files\\Adobe\\Adobe Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe',  # Windows
            f'{letter}:\\Program Files (x86)\\Steam\\steamapps\\common\\Substance 3D Painter {year}\\Adobe Substance 3D Painter.exe'  # Windows Steam
        ])

  # Check each path for the current operating system and return the first one that exists
  for path in paths:
    path = os.path.expanduser(path)
    if Path(path).exists():
      return path

  # If none of the paths exist, return an empty string
  return ''

# @Operators

class OpenInSubstancePainterOperator(bpy.types.Operator):
  """Open Collection in Substance Painter"""
  bl_idname, bl_label = 'st.open_in_substance_painter', 'Open Collection in Substance Painter'

  def execute(self, context):
    preferences = context.preferences.addons[__name__].preferences

    if preferences.painter_path == '':
      self.report({'ERROR'}, 'Please specify Substance Painter path in addon preferences')
      return {'FINISHED'}

    if bpy.data.filepath == '':
      self.report({'ERROR'}, 'File is not saved. Please save your blend file')
      return {'FINISHED'}

    directory, file = get_paths()

    for o in bpy.context.view_layer.active_layer_collection.collection.objects:
      # Check if the object is mesh:
      if o.type != 'MESH':
        self.report({'ERROR'}, f'Object {o.name} is not a mesh')
        return {'FINISHED'}

      # Check if the object has a material:
      if len(o.data.materials) == 0 or o.data.materials[0] is None:
        self.report({'ERROR'}, f'Object {o.name} has no material assigned')
        return {'FINISHED'}

    textures_output_path = Path(directory).joinpath(preferences.texture_output_folder_name)

    if not textures_output_path.exists():
      textures_output_path.mkdir(parents=True, exist_ok=True)

    fbx_path = directory + file + '.fbx'

    # Export FBX
    bpy.ops.wm.save_mainfile()
    bpy.ops.export_scene.fbx(
      mesh_smooth_type='EDGE',
      use_mesh_modifiers=True,
      add_leaf_bones=False,
      apply_scale_options='FBX_SCALE_ALL',
      use_batch_own_dir=False,
      bake_anim_use_nla_strips=False,
      bake_space_transform=True,
      batch_mode="COLLECTION",
      filepath=directory
    )

    # Check if a mac .app and add the executable part automatically
    if os.name == 'posix' and preferences.painter_path.endswith('.app'):
      preferences.painter_path = preferences.painter_path + '/Contents/MacOS/Adobe Substance 3D Painter'
    
    # Check if preferences.painter_path exists
    if not Path(preferences.painter_path).exists():
      self.report({'ERROR'}, 'Substance Painter path is not valid. Please set the corrent path to Substance Painter in addon preferences')
      return {'FINISHED'}

    spp_path = directory + file + '.spp'

    # Escape the painter path on posix
    if os.name == 'posix':
      painter_path = re.sub(r'(?<!\\) ', r'\ ', preferences.painter_path)
    else:
      painter_path = preferences.painter_path

    # Parse the environment variable
    # env_override = preferences.env.split(';')
    # env_override = [e.split('=') for e in env_override]
    # env_override = {e[0]: e[1] if len(e) > 1 else '' for e in env_override}
    # env = os.environ.copy()
    # env.update(env_override)

    try:
      if os.name == 'nt':
        subprocess.Popen([painter_path, '--mesh', fbx_path, '--export-path', str(textures_output_path), spp_path])
      else:
        subprocess.Popen(f'{painter_path} --mesh {fbx_path} --export-path {str(textures_output_path)} {spp_path}', shell=True)

    except Exception as e:
      self.report({'ERROR'}, f'Error opening Substance Painter: {e}')
      return {'FINISHED'}

    return {'FINISHED'}

class LoadSubstancePainterTexturesOperator(bpy.types.Operator):
  """Load Substance Painter Textures"""
  bl_idname, bl_label, bl_options = 'st.load_substance_painter_textures', 'Load Substance Painter Textures', {'REGISTER', 'UNDO'}

  def execute(self, context):
    # Check that node wrangler is enabled
    if 'node_wrangler' not in bpy.context.preferences.addons:
      self.report({'ERROR'}, 'Node Wrangler needs to be enabled! Please enable it in Edit -> Preferences -> Add-ons')
      return {'FINISHED'}

    previous_context = context.area.type
    context.area.type = 'NODE_EDITOR'
    context.area.ui_type = 'ShaderNodeTree'
    preferences = context.preferences.addons[__name__].preferences
    directory, file = get_paths()
    textures_output_path = Path(directory).joinpath(preferences.texture_output_folder_name)

    # All of the materials in the blend file
    material_names = [material.name for material in bpy.data.materials]

    # Reload old textures first
    for item in bpy.data.images: item.reload()

    # Return if the file is not save
    if bpy.data.filepath == '':
      self.report({'ERROR'}, 'File is not saved')
      context.area.type = previous_context
      return {'FINISHED'}

    # Return if the texture folder doesn't exist
    if not textures_output_path.exists():
      self.report({'ERROR'}, 'There is no texture folder')
      context.area.type = previous_context
      return {'FINISHED'}

    # Return if there are no materials in the scene
    if len(bpy.data.materials) == 0:
      self.report({'ERROR'}, 'There are no materials in the scene')
      context.area.type = previous_context
      return {'FINISHED'}

    # Iterate through all of the files and group them by texture set name (material)
    texture_sets = defaultdict(list)
    for texture_file in textures_output_path.iterdir():
      regex_search_result = re.search(preferences.texture_set_name_regex, texture_file.name)
      if regex_search_result:
        texture_set_name = regex_search_result.group(1)
        texture_sets[texture_set_name].append(texture_file.name)

    # Set any mesh object as an active one so that we could use it while we're loading textures
    # for different materials (because you need to use Shader Editor and can't assign directly)
    for obj in bpy.data.objects:
      if obj.type == 'MESH' and len(obj.data.materials) > 0:
        context.view_layer.objects.active = obj
        break
    if context.active_object.type != 'MESH':
      self.report({'ERROR'}, 'There are no meshes in the scene')
      context.area.type = previous_context
      return {'FINISHED'}

    # Material to switch back to when we're done adding textures
    prev_material = context.object.data.materials[0]
    # For all of the texture sets that have a material with matching name add nodes via node wrangler
    for texture_set_name, texture_file_names in texture_sets.items():
      if texture_set_name in material_names:
        # Set node editor to current material
        material = bpy.data.materials[texture_set_name]
        context.object.data.materials[0] = material
        context.space_data.node_tree = material.node_tree
        # Don't add textures if there're more than 2 nodes in the tree (if textures were already added)
        if len(context.space_data.node_tree.nodes) > 2:
          self.report({'INFO'}, f'Material {material.name} has more than 2 nodes, skipping')
          continue
        # Select the Principled BSDF node
        for node in context.space_data.node_tree.nodes:
          if node.bl_idname == 'ShaderNodeBsdfPrincipled':
            context.space_data.node_tree.nodes.active = node
            break
        # Adding textures to node tree
        bpy.ops.node.nw_add_textures_for_principled(directory=f'{textures_output_path}{os.sep}', files=[{'name':n} for n in texture_file_names])
    context.object.data.materials[0] = prev_material
    context.area.type = previous_context
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
    directory, file = get_paths()
    fbx_path = directory + file + '.fbx'

    row = layout.row()

    fbx_exists = Path(fbx_path).exists()

    if file == 'Scene_Collection':
      row.label(text='Select a collection in the outliner')
    else:
      if fbx_exists:
        row = layout.row()
        row.label(text='Press Ctrl+Shift+R in Painter after re-export to reload the model')
      text = f'Re-Export "{file}"' if fbx_exists else f'Export "{file}" to Painter'
      row = layout.row()
      row.operator('st.open_in_substance_painter', text=text)

    row = layout.row()
    row.operator('st.load_substance_painter_textures', text='Load Painter Textures')

# @Preferences

class SubstanceToolsPreferences(bpy.types.AddonPreferences):
  bl_idname = __name__

  painter_path: bpy.props.StringProperty(name='Substance Painter Executable Path', default=detect_substance_painter_path(), subtype='FILE_PATH')
  texture_output_folder_name: bpy.props.StringProperty(name='Textures Folder Name', default='textures')
  # Material names cant have underscores
  texture_set_name_regex: bpy.props.StringProperty(name='Texture Set Name Regex', default='(.+?)_')
  # env: bpy.props.StringProperty(name='Environment', default='')

  def draw(self, context):
    layout = self.layout
    layout.prop(self, 'painter_path')
    layout.prop(self, 'texture_output_folder_name')
    layout.prop(self, 'texture_set_name_regex')
    # layout.prop(self, 'env')

# @Register

classes = (
  OpenInSubstancePainterOperator,
  LoadSubstancePainterTexturesOperator,

  SubstanceToolsPanel,

  SubstanceToolsPreferences
)

def register():
  for c in classes: bpy.utils.register_class(c)

def unregister():
  for c in classes: bpy.utils.unregister_class(c)

if __name__ == '__main__': register()