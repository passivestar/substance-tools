# Substance Import-Export Tools

<img width="960" alt="substancetools" src="https://github.com/passivestar/substance-tools/assets/60579014/0e13aa12-3ddd-4151-bbbc-dae41137027a">

https://github.com/passivestar/substance-tools/assets/60579014/b47d8e04-7535-4510-aed2-9c4569880b02


## Installation

- Click on "Releases" on the right and download zip
- Go to `Edit -> Preferences -> Addons`
- Press `Install...`
- Select the archive

In 3D view press N. You'll find new buttons in the menu on the right on the "Substance" tab

# Usage

- Put objects you want to texture into a collection and give them materials. Individual materials will become texture sets in Painter!
- Click on the collection you want to texture in the outliner
- Press the `Export [Collection Name] to Painter` button
- When you're done, export textures from Painter (`Ctrl+Shift+E`), and press `Load Painter Textures` in Blender ✨

Keep in mind that:
- If you use a custom output template, make sure the exported textures' filenames start with the texture set name, like this: `$textureSet_diff(_$colorSpace)(.$udim)`
- In Blender you can link objects to a collection instead of moving them if you hold `Ctrl` when you drag them in the outliner. This way you can create collections specifically for Substance Painter export and group assets however you like!

# Preferences

In the addon preferences you can configure:

- Substance Painter Path (in case it wasn't automatically detected)
- Texture output folder name. Default is `textures`
- Texture Set Name Regex - Regular expression used to determine the texture set name by the texture file name. Usually the texture set name goes first and is separated from other info by the first "_". Default value is `(.+?)_`
