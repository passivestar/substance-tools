# Substance Tools

https://github.com/passivestar/substance-tools/assets/60579014/b47d8e04-7535-4510-aed2-9c4569880b02


## Installation

- Click on "Releases" on the right and download zip
- Go to `Edit -> Preferences -> Addons`
- Press `Install...`
- Select the archive

In 3D view press N. You'll find new buttons in the menu on the right on the "Substance" tab

# Usage

- Specify the path to Substance Painter executable in the addon preferences
- Place objects you want to texture into their own separate collection and give them materials. Individual materials will become textures sets in Substance!
- Export your file to FBX with batching by collection enabled (Or enable the "Auto Export FBX" option in the addon settings)
- Click on the collection you want to texture in the outliner
- Press the `Open [Collection Name] in Painter` button
- In Substance Painter, press `Ctrl+S` to save the `.spp` file
- If you use a custom output template, make sure the exported textures filenames start with the texture set name, like this: `$textureSet_diff(_$colorSpace)(.$udim)`
- When you're done, export textures in substance (`Ctrl+Shift+E`), and press `Load Painter Textures` in Blender. Make sure you have `Node Wrangler` addon enabled for it to work.

Pro Tip:
In Blender you can link objects to a collection instead of moving if you hold `Ctrl` when you drag them in the outliner. This way you can create collections specifically for Substance export and group assets however you like!

# Preferences

In the addon preferences you can configure:

- Substance Painter Path
- Texture output folder name. Default is `textures`
- Texture Set Name Regex - Regular expression used to determine the texture set name by the texture file name. Usually the texture set name goes first and is separated from other info by the first "_". Default value is `(.+?)_`
- Auto Export FBX - Automatically export collections when opening the active collection in Substance
