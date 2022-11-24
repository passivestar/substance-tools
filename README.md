# Substance Tools

<img width="453" alt="image" src="https://user-images.githubusercontent.com/60579014/203778567-10ea89ff-7c1d-468f-8d12-64f1ddf74138.png">

## Installation

- Download zip
- Go to `Edit -> Preferences -> Addons`
- Press `Install...`
- Select the archive

In 3D view press N. You'll be able to find new buttons in the menu on the right.

# Usage

- Specify the path to Substance Painter in the addon preferences
- Place objects you want to texture into their own separate collection and give them a material. You can link objects to collection instead of moving if you hold ctrl when you drag them in the outliner
- Export your file to FBX with batching by collection enabled
- Select the collection you want to texture in the outliner
- Press `Open Collection in Painter`
- In Substance Painter, first press `Ctrl+S` to save the `.spp` file
- Make sure exported textures start with the texture set name, like this: `$textureSet_diff(_$colorSpace)(.$udim)`
- When you're done, export textures in substance, and press `Load Painter Textures` in Blender. Make sure you have `Node Wrangler` addon enabled.

# Preferences

In the addon preferences you can configure:

- Substance Painter Path
- Texture output folder name. Default is `textures`
- Texture Set Name Regex - Regular expression used to determine the texture set name by the texture file name. Usually the texture set name goes first and is separated from other info by the first "_". Default value is `(.+?)_`
