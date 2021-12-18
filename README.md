# Substance Integration Tools

## Installation

- Download zip
- Go to `Edit -> Preferences -> Addons`
- Press `Install...`
- Select the archive

In 3D view press N. You'll be able to find new buttons in the menu on the right.

# Operators

This addon has the following operators:

## Open In Substance Painter

Does the following:
- Exports the current scene in fbx (in the same folder as the current blend file)
- Creates a folder for Substance texture output (name can be configured)
- Launches Substance Painter with mesh set to the exported fbx file, output folder set to the created texture output folder, and spp file name set to the name of the current blend file

If the texture output folder already exists, just reexport fbx. This way you can use the same button on your first export, and on your subsequent exports. Please note that even though it sets the correct spp file name, you'll still have to press Ctrl+S to save the file yourself after Substance Painter opens. There's currently no way of making Substance save the file

## Load Substance Painter Textures
This operator requires the Node Wrangler addon to be enabled (Node Wrangler ships with blender).

Does the following:
- Iterates through all of the files in the texture output folder and groups them by texture set name (material)
- For every texture set in the texture output folder looks for a material in the current blend file with a matching name and adds matching textures to them. Ignores materials that already have textures in them.
- Reloads all of the textures that already existed in the blend file.

You can use this operator to either load textures that were not loaded yet, or reload textures that were already imported with this single operator.

# Preferences

In the addon preferences you can configure:

- Substance Painter Path. Default is `C:\Program Files\Allegorithmic\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe`
- Texture output folder name. Default is `substance_painter_textures`
- Texture Set Name Regex - Regular expression used to determine the texture set name by the texture file name. Usually the texture set name goes first and is separated from other info by the first "_". Default value is `(.+?)_`