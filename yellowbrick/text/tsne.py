# yellowbrick.text.tsne
# Implements TSNE visualizations of documents in 2D space.
#
# Author:   Benjamin Bengfort <benjamin@bengfort.com>
# Created:  Mon Feb 20 06:33:29 2017 -0500
#
# Copyright (C) 2016 Bengfort.com
# For license information, see LICENSE.txt
#
# ID: tsne.py [] benjamin@bengfort.com $

"""
Implements TSNE visualizations of documents in 2D space.
"""

##########################################################################
## Imports
##########################################################################

import numpy as np
import matplotlib.pyplot as plt

from collections import defaultdict

from yellowbrick.text.base import TextVisualizer
from yellowbrick.exceptions import YellowbrickValueError
from yellowbrick.style.colors import resolve_colors, get_color_cycle

from sklearn.manifold import TSNE
from sklearn.pipeline import Pipeline
from sklearn.decomposition import TruncatedSVD, PCA

##########################################################################
## Quick Methods
##########################################################################

def tsne(X, y=None, ax=None, decompose='svd', decompose_by=50, classes=None,
           colors=None, colormap=None, **kwargs):
    """
    Display a projection of a vectorized corpus in two dimensions using TSNE,
    a nonlinear dimensionality reduction method that is particularly well
    suited to embedding in two or three dimensions for visualization as a
    scatter plot. TSNE is widely used in text analysis to show clusters or
    groups of documents or utterances and their relative proximities.

    Parameters
    ----------

    X : ndarray or DataFrame of shape n x m
        A matrix of n instances with m features representing the corpus of
        vectorized documents to visualize with tsne.

    y : ndarray or Series of length n
        An optional array or series of target or class values for instances.
        If this is specified, then the points will be colored according to
        their class. Often cluster labels are passed in to color the documents
        in cluster space, so this method is used both for classification and
        clustering methods.

    ax : matplotlib axes
        The axes to plot the figure on.

    decompose : string or None
        A preliminary decomposition is often used prior to TSNE to make the
        projection faster. Specify `"svd"` for sparse data or `"pca"` for
        dense data. If decompose is None, the original data set will be used.

    decompose_by : int
        Specify the number of components for preliminary decomposition, by
        default this is 50; the more components, the slower TSNE will be.

    classes : list of strings
        The names of the classes in the target, used to create a legend.

    colors : list or tuple of colors
        Specify the colors for each individual class

    colormap : string or matplotlib cmap
        Sequential colormap for continuous target

    kwargs : dict
        Pass any additional keyword arguments to the TSNE transformer.

    Returns
    -------
    ax : matplotlib axes
        Returns the axes that the parallel coordinates were drawn on.
    """
    # Instantiate the visualizer
    visualizer = TSNEVisualizer(
        ax, decompose, decompose_by, classes, colors, colormap, **kwargs
    )

    # Fit and transform the visualizer (calls draw)
    visualizer.fit(X, y, **kwargs)
    visualizer.transform(X)

    # Return the axes object on the visualizer
    return visualizer.ax


##########################################################################
## TSNEVisualizer
##########################################################################

class TSNEVisualizer(TextVisualizer):
    """
    Display a projection of a vectorized corpus in two dimensions using TSNE,
    a nonlinear dimensionality reduction method that is particularly well
    suited to embedding in two or three dimensions for visualization as a
    scatter plot. TSNE is widely used in text analysis to show clusters or
    groups of documents or utterances and their relative proximities.

    TSNE will return a scatter plot of the vectorized corpus, such that each
    point represents a document or utterance. The distance between two points
    in the visual space is embedded using the probability distribution of
    pairwise similarities in the higher dimensionality; thus TSNE shows
    clusters of similar documents and the relationships between groups of
    documents as a scatter plot.

    TSNE can be used with either clustering or classification; by specifying
    the ``classes`` argument, points will be colored based on their similar
    traits. For example, by passing ``cluster.labels_`` as ``y`` in ``fit()``, all
    points in the same cluster will be grouped together. This extends the
    neighbor embedding with more information about similarity, and can allow
    better interpretation of both clusters and classes.

    For more, see https://lvdmaaten.github.io/tsne/

    Parameters
    ----------

    ax : matplotlib axes
        The axes to plot the figure on.

    decompose : string or None
        A preliminary decomposition is often used prior to TSNE to make the
        projection faster. Specify `"svd"` for sparse data or `"pca"` for
        dense data. If decompose is None, the original data set will be used.

    decompose_by : int
        Specify the number of components for preliminary decomposition, by
        default this is 50; the more components, the slower TSNE will be.

    classes : list of strings
        The names of the classes in the target, used to create a legend.

    colors : list or tuple of colors
        Specify the colors for each individual class

    colormap : string or matplotlib cmap
        Sequential colormap for continuous target

    kwargs : dict
        Pass any additional keyword arguments to the TSNE transformer.
    """

    def __init__(self, ax=None, decompose='svd', decompose_by=50, classes=None,
               colors=None, colormap=None, **kwargs):
        """
        Initialize the TSNE visualizer with visual hyperparameters.
        """
        super(TSNEVisualizer, self).__init__(ax=ax, **kwargs)

        # Visualizer parameters
        self.classes_ = classes
        self.n_instances_ = 0

        # Visual Parameters
        # TODO: Only colors currently works to select the colors of classes.
        self.colors = colors
        self.colormap = colormap

        # TSNE Parameters
        self.transformer_ = self.make_transformer(decompose, decompose_by, kwargs)

    def make_transformer(self, decompose='svd', decompose_by=50, tsne_kwargs={}):
        """
        Creates an internal transformer pipeline to project the data set into
        2D space using TSNE, applying an pre-decomposition technique ahead of
        embedding if necessary. This method will reset the transformer on the
        class, and can be used to explore different decompositions.

        Parameters
        ----------

        decompose : string or None
            A preliminary decomposition is often used prior to TSNE to make the
            projection faster. Specify `"svd"` for sparse data or `"pca"` for
            dense data. If decompose is None, the original data set will be used.

        decompose_by : int
            Specify the number of components for preliminary decomposition, by
            default this is 50; the more components, the slower TSNE will be.

        Returns
        -------

        transformer : Pipeline
            Pipelined transformer for TSNE projections
        """

        decompositions = {
            'svd': TruncatedSVD,
            'pca': PCA,
        }

        if decompose and decompose.lower() not in decompositions:
            raise YellowbrickValueError(
                "'{}' is not a valid decomposition, use {}, or None".format(
                    decompose, ", ".join(decompositions.keys())
                )
            )

        # Create the pipeline steps
        steps = []

        # Add the pre-decomposition
        if decompose:
            klass = decompositions[decompose]
            steps.append((decompose, klass(n_components=decompose_by)))

        # Add the TSNE manifold
        steps.append(('tsne', TSNE(n_components=2, **tsne_kwargs)))

        # return the pipeline
        return Pipeline(steps)

    def fit(self, X, y=None, **kwargs):
        """
        The fit method is the primary drawing input for the TSNE projection
        since the visualization requires both X and an optional y value. The
        fit method expects an array of numeric vectors, so text documents must
        be vectorized before passing them to this method.

        Parameters
        ----------
        X : ndarray or DataFrame of shape n x m
            A matrix of n instances with m features representing the corpus of
            vectorized documents to visualize with tsne.

        y : ndarray or Series of length n
            An optional array or series of target or class values for
            instances. If this is specified, then the points will be colored
            according to their class. Often cluster labels are passed in to
            color the documents in cluster space, so this method is used both
            for classification and clustering methods.

        kwargs : dict
            Pass generic arguments to the drawing method

        Returns
        -------
        self : instance
            Returns the instance of the transformer/visualizer
        """

        # If we don't have classes already stored, store them.
        if y and self.classes_ is None:
            self.classes_ = [str(label) for label in set(y)]

        # Fit our internal transformer and transform the data.
        vecs = self.transformer_.fit_transform(X)
        self.n_instances_ += vecs.shape[0]

        # Draw the vectors
        self.draw(vecs, y, **kwargs)

        # Fit always returns self.
        return self

    def draw(self, points, target=None, **kwargs):
        """
        Called from the fit method, this method draws the TSNE scatter plot,
        from a set of decomposed points in 2 dimensions. This method also
        accepts a third dimension, target, which is used to specify the colors
        of each of the points. If the target is not specified, then the points
        are plotted as a single cloud to show similar documents.
        """

        # Create the axis if it doesn't exist
        if self.ax is None: self.ax = plt.gca()

        # Create the color mapping for the classes.
        # TODO: Allow both colormap, listed colors, and palette definition
        # See the FeatureVisualizer for more on this.
        color_values = get_color_cycle()
        classes = self.classes_ or [None]
        colors = dict(zip(classes, color_values))

        # Expand the points into vectors of x and y for scatter plotting,
        # assigning them to their label if the label has been passed in.
        # Additionally, filter classes not specified directly by the user.
        series = defaultdict(lambda: {'x':[], 'y':[]})
        if self.classes_: classes = frozenset(self.classes_)

        if target:
            for label, point in zip(target, points):
                if self.classes_ and label not in classes:
                    continue

                series[label]['x'].append(point[0])
                series[label]['y'].append(point[1])
        else:
            for x,y in points:
                series[None]['x'].append(x)
                series[None]['y'].append(y)

        # Plot the points
        for label, points in series.items():
            self.ax.scatter(points['x'], points['y'], c=colors[label], alpha=0.7, label=label)

    def finalize(self, **kwargs):
        """
        Finalize the drawing by adding a title and legend, and removing the
        axes objects that do not convey information about TNSE.
        """

        # Add a title
        self.set_title(
            "TSNE Projection of {} Documents".format(self.n_instances_)
        )

        # Remove the ticks
        self.ax.set_yticks([])
        self.ax.set_xticks([])

        # Add the legend outside of the figure box.
        if self.classes_:
            box = self.ax.get_position()
            self.ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
            self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
