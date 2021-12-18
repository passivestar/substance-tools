import bpy, re, subprocess, os
from collections import defaultdict
from pathlib import Path

bl_info = {
  'name': 'Substance Import-Export Tools',
  'version': (1, 0, 0),
  'author': 'passivestar',
  'blender': (3, 0, 0),
  'location': '3D View N Panel',
  'description': 'Simplifies Export to Substance Painter',
  'category': 'Import-Export'
}

# @Util

def get_paths():
  directory = bpy.path.abspath('//')
  file = bpy.path.basename(bpy.data.filepath).split('.')[0]
  return ( directory, file )

# @Operators

class OpenInSubstancePainterOperator(bpy.types.Operator):
  """Open in Substance Painter"""
  bl_idname, bl_label = 'st.open_in_substance_painter', 'Export FBX to Substance Painter'

  def execute(self, context):
    preferences = context.preferences.addons[__name__].preferences
    if preferences.painter_path == '':
      self.report({'ERROR'}, 'Please specify Substance Painter exe path in addon preferences')
      return {'FINISHED'}
    if bpy.data.filepath == '':
      self.report({'ERROR'}, f'File is not saved. Please save your blend file')
      return {'FINISHED'}
    directory, file = get_paths()
    bpy.ops.export_scene.fbx(
        mesh_smooth_type='EDGE',
        use_mesh_modifiers=False,
        add_leaf_bones=False,
        bake_anim_use_nla_strips=False,
        filepath=directory + file + '.fbx'
      )
    textures_output_path = Path(directory).joinpath(preferences.texture_output_folder_name)
    if not textures_output_path.exists():
      textures_output_path.mkdir(parents=True, exist_ok=True)
      fbx_path = directory + file + '.fbx'
      spp_path = directory + file + '.spp'
      subprocess.Popen([preferences.painter_path, '--mesh', fbx_path, '--export-path', str(textures_output_path), spp_path])
    return {'FINISHED'}

class LoadSubstancePainterTexturesOperator(bpy.types.Operator):
  """Load Substance Painter Textures"""
  bl_idname, bl_label, bl_options = 'st.load_substance_painter_textures', 'Load Substance Painter Textures', {'REGISTER', 'UNDO'}

  def execute(self, context):
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
      self.report({'ERROR'}, f'File is not saved')
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
      texture_set_name = re.search(preferences.texture_set_name_regex, texture_file.name).group(1)
      texture_sets[texture_set_name].append(texture_file.name)

    # Set any mesh object as an active one so that we could use it while we're loading textures
    # for different materials (because you need to use Shader Editor and can't assign directly)
    for obj in bpy.data.objects:
      if obj.type == 'MESH':
        context.view_layer.objects.active = obj
        break
    if context.active_object.type != 'MESH':
      self.report({'ERROR'}, f'There are no meshes in the scene')
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
  bl_label = 'Substance Painter Tools'
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = 'Substance'

  def draw(self, context):
    layout = self.layout
    row = layout.row()
    row.operator('st.open_in_substance_painter', text='Export to Painter')
    row = layout.row()
    row.operator('st.load_substance_painter_textures', text='Load Painter Textures')

# @Preferences

painter_default_path = 'C:\Program Files\Allegorithmic\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe'

class SubstanceToolsPreferences(bpy.types.AddonPreferences):
  bl_idname = __name__

  painter_path: bpy.props.StringProperty(name='Substance Painter Executable Path', default=painter_default_path, subtype='FILE_PATH')
  texture_output_folder_name: bpy.props.StringProperty(name='Textures Folder Name', default='substance_painter_textures')
  # Material names cant have underscores
  texture_set_name_regex: bpy.props.StringProperty(name='Texture Set Name Regex', default='(.+?)_')

  def draw(self, context):
    layout = self.layout
    layout.prop(self, 'painter_path')
    layout.prop(self, 'texture_output_folder_name')
    layout.prop(self, 'texture_set_name_regex')

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