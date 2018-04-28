from astropy.visualization import ZScaleInterval
from bokeh.io import output_notebook
from bokeh.layouts import row, column
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper, TapTool
from bokeh.models.tickers import BasicTicker
from bokeh.models.widgets import Select
from bokeh.palettes import gray
from bokeh.plotting import figure
from bokeh.resources import INLINE
import numpy as np

import lsst.afw.geom as afwGeom

output_notebook(INLINE, hide_banner=True)

pixel_radius_names = ["3_0", "4_5", "6_0", "9_0", "12_0", "17_0", "25_0", "35_0", "50_0", "70_0"]
pixel_radius = np.array([float(x.replace('_', '.')) for x in pixel_radius_names])

class source_plots(object):
    """
    This is the main class for setting up and handling interactive plots using Bokeh.
    """
    def __init__(self, butler):
        """
        Initialize the class.

        Parameters
        ----------
        butler : lsst.daf.persistence.Butler
            An instance of the Butler to use for the data in the plots.
        """
        self.butler = butler
        self.calexp = None
        self.calib = None
        self.dataid = None
        self.good_indexes = None
        self.src = None
        self.zscale = ZScaleInterval()
        self.setup_widgets()
        self.setup_plots()

        # These are the statements that make interactiveness possible.
        self.dataid_selector.on_change('value', self.select_dataid)
        self.star_gal_sep_src.on_change('selected', self.make_selection)

    def fill_dataid_selector(self):
        """
        Query the Butler for all of the dataid's associated with the *calexp* data type and add
        them to the Select widget.
        """
        keys = list(self.butler.getKeys('calexp'))
        values = self.butler.queryMetadata('calexp', keys)
        selections = ['']
        for value in values:
            selections.append("; ".join(["{}: {}".format(k, v) for k, v in zip(keys, value)]))
        self.dataid_selector.options = selections

    def make_plot(self, doc):
        """
        Layout all of the widgets and plots onto the provided Bokeh document.

        Parameters
        ----------
        doc : Bokeh doc instance
            The Bokeh document in which to add all of the widgets and plots.
        """
        right_col = column(self.img_plt, self.radial_plt)
        layout = column(self.dataid_selector, row(self.sg_sep_plt, right_col))
        doc.add_root(layout)
        doc.title = "Interactive Star-Galaxy Separation Plot"

    def make_postage_stamp_plot(self, index, stamp_size=100, reverse_colormap=False):
        """
        Gather the data for creating the source postage stamp plot.

        Parameters
        ----------
        index : int
            The location of the source data in the Source table.
        stamp_size : int, optional
            Size of the generated postage stamp in pixels.
        reverse_colormap : bool, optional
            Reverse the colormap. Default is black (low) to white (high).
        """
        ra_target, dec_target = self.src['coord_ra'][index], self.src['coord_dec'][index]  # Radians
        radec = afwGeom.SpherePoint(ra_target, dec_target, afwGeom.radians)
        cutoutSize = afwGeom.ExtentI(stamp_size, stamp_size)
        wcs = self.calexp.getWcs()
        # Note: This call fails in version 15.0. Requires a weekly after that release.
        xy = afwGeom.PointI(wcs.skyToPixel(radec))
        bbox = afwGeom.BoxI(xy - cutoutSize // 2, cutoutSize)
        # Check for bounds that fall off the edges of the image. Need to clip them to the
        # image boundary otherwise the calexp_sub call fails.
        calexp_extent = self.calexp.getDimensions()
        clipped_bbox = afwGeom.BoxI(afwGeom.PointI(0, 0), calexp_extent)
        clipped_bbox.clip(bbox)
        # Postage stamp image only
        cutout_image = self.butler.get('calexp_sub', bbox=clipped_bbox, immediate=True,
                                       dataId=self.dataid).getMaskedImage()
        vmin, vmax = self.zscale.get_limits(cutout_image.image.array)
        self.image_src.data = {'img': [cutout_image.image.array], 'x': [0], 'y': [0],
                               'dw': [clipped_bbox.getDimensions().getX()],
                               'dh': [clipped_bbox.getDimensions().getY()]}
        gc = gray(256)
        if reverse_colormap:
            gc.reverse()
        lcm = LinearColorMapper(palette=gc, low=vmin, high=vmax)
        self.img_plt.image('img', 'x', 'y', 'dw', 'dh', color_mapper=lcm, source=self.image_src)
        # Color bar doesn't come up properly. Need to work on this later.
        colorbar = ColorBar(color_mapper=lcm, ticker=BasicTicker(), border_line_color=None,
                            label_standoff=5, location=(0, 0))
        # self.img_plt.add_layout(colorbar, 'right')
        # Does the cutout_image have a wcs? It does not appear to...
        self.img_plt.circle(xy.getX() - cutout_image.getX0(), xy.getY() - cutout_image.getY0(),
                            fill_color=None, line_color='red', radius=int(0.05 * stamp_size))

    def make_radial_plot(self, index):
        """
        Create the plot of pixel area normalize circular aperture flux versus pixel radius.

        Parameters
        ----------
        index : int
            The location of the source data in the Source table.
        """
        caf_schema_names = ["base_CircularApertureFlux_{}_flux".format(x) for x in pixel_radius_names]
        # IMPROVEMENT: Use the sigmas to draw error bars on the plot.
        #caf_sigma_schema_names = ["base_CircularApertureFlux_{}_fluxSigma"
        #                           .format(x) for x in pixel_radius_names]
        #caf_flag_schema_names = ["base_CircularApertureFlux_{}_flag".format(x) for x in pixel_radius_names]

        ca_fluxes = np.array([self.src[name][index] for name in caf_schema_names])
        #ca_fluxSigmas = np.array([self.src[name][index] for name in caf_sigma_schema_names])
        #caf_flags = np.array([self.src[name][index] for name in caf_flag_schema_names])
        good_fluxes = np.isfinite(ca_fluxes)
        pixel_area = np.pi * pixel_radius**2
        norm_ca_fluxes = ca_fluxes[good_fluxes] / pixel_area[good_fluxes]
        plot_x = pixel_radius[good_fluxes]
        self.caf_src.data = {'pix_rad': plot_x, 'caf': norm_ca_fluxes}

    def make_selection(self, attrname, old, new):
        """
        Get the selected index from the star-galaxy plot and pass it on to the postage stamp and
        radial plot generator functions. Note: If more than one glyph is selected, the function only
        passes the first one on.

        Parameters
        ----------
        attrname : str
            The attribute name specified by the star-galaxy separation ColumnDataSource
            *on_change* function.
        old : object
            Possibly the original, unchanged data. Unclear from Bokeh documentation.
        new : object
            Not clear from Bokeh documentation what type of object this is. It does contain the
            currently selected indicies within the associated data structure.
        """
        index = None
        try:
            index = new['1d']['indices'][0]
        except IndexError:
            return
        self.make_postage_stamp_plot(index)
        self.make_radial_plot(index)

    def make_star_galaxy_separation_plot(self):
        """
        Create the star-galaxy separation plot. This plots PSF magnitudes versus PSF magnitudes
        minus Model magnitudes. The points are then color coded by the extendedness classification
        value.
        """
        self.calexp = self.butler.get('calexp', dataId=self.dataid)
        self.calib = self.calexp.getCalib()
        self.src = self.butler.get('src', dataId=self.dataid)

        fluxes = self.src.getPsfFlux()
        good_indexes = np.logical_and(fluxes > 0.0, np.isfinite(fluxes))
        # Model fluxes also need to check for negative and bad values.
        model_fluxes = self.src.getModelFlux()
        good_model_indexes = np.logical_and(model_fluxes > 0.0, np.isfinite(model_fluxes))

        self.good_indexes = np.logical_and(good_indexes, good_model_indexes)

        psf_mag = self.calib.getMagnitude(fluxes[self.good_indexes])
        cm_mag = self.calib.getMagnitude(model_fluxes[self.good_indexes])

        extendedness = self.src['base_ClassificationExtendedness_value'][self.good_indexes]
        colors = []
        label = []
        for x in extendedness:
            if x == 0.0:
                colors.append('blue')
                label.append('star')
            elif x == 1.0:
                colors.append('red')
                label.append('galaxy')
            else:
                colors.append('orange')
                label.append('unknown')

        self.star_gal_sep_src.data = {'psf_mag': psf_mag, 'diff_model': psf_mag - cm_mag, 'colors': colors,
                                      'label': label}

    def select_dataid(self, attrname, old, new):
        """
        Take the selected dataid from the Select widget and turn into a dataid dict. After that,
        create the star-galaxy separation plot.

        Parameters
        ----------
        attrname : str
            The attribute name specified by the Select widget *on_change* function.
        old : object
            Possibly the original, unchanged data. Unclear from Bokeh documentation.
        new : object
            Not clear from Bokeh documentation what type of object this is. It does contain the
            currently selected indicies within the associated data structure.
        """
        if new == "":
            return
        values = new.split(';')
        id_parts = [x.split() for x in values]
        dataid = {}
        for id_part in id_parts:
            key = id_part[0].strip(':')
            try:
                value = int(id_part[1])
            except ValueError:
                value = id_part[1]
            dataid[key] = value
        self.dataid = dataid

        self.make_star_galaxy_separation_plot()

    def setup_plots(self):
        """
        Setup the necessary boilerplate for all of the plots on the main panel.
        """
        self.star_gal_sep_src = ColumnDataSource(data=dict(psf_mag=[], diff_model=[], colors=[], label=[]))
        self.image_src = ColumnDataSource(data=dict(img=[[]], x=[0], y=[0], dw=[10], dh=[10]))
        self.caf_src = ColumnDataSource(data=dict(pix_rad=[], caf=[]))

        tools = 'pan,box_zoom,reset'

        self.sg_sep_plt = figure(plot_width=600, plot_height=600, tools=tools, active_drag='box_zoom')
        self.sgsc = self.sg_sep_plt.circle('psf_mag', 'diff_model', size=15, color='colors', legend='label',
                                           source=self.star_gal_sep_src, hover_alpha=0.5)
        self.sg_sep_plt.xaxis.axis_label = "PSF Magnitude"
        self.sg_sep_plt.yaxis.axis_label = "PSF - Model Magnitude"
        # Legend functionality currently does not handle hiding when specifying by column.
        self.sg_sep_plt.legend.location = 'top_left'
        self.sg_sep_plt.legend.click_policy = "hide"

        hover = HoverTool(tooltips=[
            ("index", "$index"),
            ("(x,y)", "($x, $y)")])
        self.sg_sep_plt.add_tools(hover)

        tap = TapTool()
        self.sg_sep_plt.add_tools(tap)

        self.img_plt = figure(plot_width=300, plot_height=300)
        self.img_plt.xaxis.axis_label = "x"
        self.img_plt.yaxis.axis_label = "y"
        self.img_plt.toolbar.logo = None
        self.img_plt.toolbar_location = None

        self.radial_plt = figure(plot_width=300, plot_height=300)
        self.radial_plt.circle('pix_rad', 'caf', size=10, source=self.caf_src)
        self.radial_plt.xaxis.axis_label = "Pixel Radius"
        self.radial_plt.yaxis.axis_label = "Flux / Pixel Area"
        self.radial_plt.toolbar.logo = None
        self.radial_plt.toolbar_location = None

    def setup_widgets(self):
        """
        Initialize the widgets on the main panel.
        """
        self.dataid_selector = Select()
        self.fill_dataid_selector()
