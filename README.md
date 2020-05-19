# MekHQ Blog

This repository contains a [jekyll](https://jekyllrb.com/) template and a [python](https://www.python.org/) script that will turn a [MekHQ](https://megamek.org/) campaign save file into a beautiful looking website. Examples of the website in action can be found here:

- [Flaming Devil Monkeys](https://flaming-devil-monkeys.netlify.app)
- [The Free Company of Oriente](https://free-company-oriente.netlify.app/)

The website will produce output for selected personnel, mission and scenario write-ups, and a full TO&E. Additional information such as fiction and TRO readouts can be added as well. Virtually any aspect of the website can be customized through the Jekyll layout system, [Bootstrap](https://getbootstrap.com/), or CSS. 

## Installation

### Requirements

- **Jekyll**: follow the installation instructions [here](https://jekyllrb.com/docs/installation/) for your operating system.
- **Python 3**: Python 3 can be downloaded [here](https://www.python.org/downloads/).

### Instructions

Download a zip version of this repository using the big green button above or download one of the available releases. Alternatively, this entire repository can be used as a template for a new repository on GitHub. 

Once you have downloaded the repository, you can test that it is functioning by running the following command from the command line in the top-level directory:

```bash
jekyll serve
```

If successful, this will serve up the website locally at [http://localhost:4000/](http://localhost:4000/).

To add your campaign's information, you should open up the `process_campaign.py` file in a text editor and change the lines shown below, which are near the top of the file.

```py
#relative or absolute path to your mekhq directory including trailing /
mekhq_path = "../Programs/mekhq-0.47.5/"

#the name of your campaign file within the campaigns directory of your 
#mekhq directory
campaign_file = 'Flaming Devil Monkeys30740904.cpnx'
```

The `mekhq_path` entry should provide a relative or absolute path to your MekHQ directory. The `campaign_file` entry should contain the name of the campaign file you wish to load.

Once you have made and saved these changes, you can run the python file from the command line:

```bash
./process_campaign.py
```

This will create all of the necessary files in your `campaign` directory and add images to your `assets/images` directory. To test whether it worked properly, you can use `jekyll serve` from the command line again to load the website locally, as described above.

## Customization

### Changing the name and description of your unit

Open the `_config.yml` file and change the name and description fields to whatever you would like.

### Changing color and font settings

The color and font settings are defined at the bottom of the `site.scss` file in the `css` directory. At the bottom you should see something like this:

```css
@import url(https://fonts.googleapis.com/css?family=Comfortaa:200,300,400,700);
$headings-font-family:Comfortaa;
@import url(https://fonts.googleapis.com/css?family=Comfortaa:200,300,400,700);
$font-family-base:Comfortaa;

$primary: #303030;
$secondary:#FF550B;
$success:#015668;
$danger:#FF304F;
$info:#0F81C7;
$warning:#0DE2EA;
$light:#e8e8e8;
$dark:#000000;
```

You can change either the fonts of color settings as you like. I would recommend using [themesr.app](https://themestr.app/theme) for picking out good color themes and fonts. It will generate output that you can copy and paste to the CSS file.

### Adding fiction

You can add blot posts in the `campaign/_posts`. Follow the outline given in the example post. These blog posts are separate from the MekHQ data. If you do not wish to use this feature, you can remove or comment out the Fiction menu item from `_data/navigation.yml`.

### Choosing which personnel to load 

By default, the script will load all personnel except astechs and medics. You can change this by customizing the `roles` value at the top of the `process_campaign.py` script.

### Personnel types in menu drop-down

You can choose which kinds of personnel to display in the drop-down menu in `_data/navigation.yml`.  Comment out (with #) categories you don't want. The default setting comments out protomech pilots as an example.

### Changing banner image

Just replace `assets/images/banner_image.png` with your own image. If you don't want a banner image, then set `banner_image` to `false` in the `_config.yml` file.


### Adding units

You can use MegaMekLab to export units as HTML files to `campaign/_tro`. In order to be read properly you should add in a YAML header as per the example file and remove the \<html\>, \<body\>, and \<div\> opening and closing tags at the top and bottom. If you provide a slug value in the YAML that matches the unit-slug in a given personnel file, a link will be made from a person's record anytime a unit is listed.

### Further customization

Because the website is written in Jekyll using Bootstrap and CSS, you can customize the look of it virtually however you want if you know how.

## Hosting

The website is produced as a static website and thus has very simple hosting requirements. I recommend [netlify](https://www.netlify.com/), but there are other free or cheap options as well.

To create your static website, type the following into your command line:

```bash
jekyll build
```

This will build your static website in the `_site` directory. You can take everything in that directory and place it wherever you want your static website hosted. Alternatively, if you installed via GitHub, many services like [netlify](https://www.netlify.com/) can deploy directly from your jekyll setup.

## Disclaimers

- I am providing this because it may be of interest, but it was designed for my own personal campaigns and in this early stage is likely to break for others, given the complexity of options in MekHQ. If your campaign will not process, please post an issue that includes the attached campaign file. 
- I am open to adding additional features to this website which may be requested through the issues tab. However, the goal here is not reproduce every possible thing that MekHQ reports but rather to produce a nice narratively driven website front for your campaign. I will not bloat this produce or provide endless customization options to satisfy BOCD ("Battletech OCD"). 
